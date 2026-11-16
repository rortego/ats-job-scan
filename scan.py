"""Scan the public job boards of a list of companies and keep the roles a candidate
outside the US can actually apply to.

Many companies publish their openings through Greenhouse, Lever or Ashby, and all three
expose a public, read-only JSON endpoint per company. This script reads those endpoints,
normalises the three formats and filters by location and title.

Run: python scan.py companies.txt
Output: all_jobs.json (everything read) and shortlist.csv (after filters).
"""
import concurrent.futures as cf
import csv
import json
import re
import sys
import urllib.request

# Locations that admit a candidate based in Latin America. Edit for another region.
LOCATION = re.compile(
    r"argentin|buenos aires|latam|latin america|south america|americas|anywhere|worldwide|global", re.I)
# Titles left out: engineering and other roles outside the search.
EXCLUDE = re.compile(
    r"engineer|developer|scientist|intern\b|junior|architect|devops|recruit|counsel|legal|designer|"
    r"researcher|security|accountant|account executive|sdr\b|bdr\b|software", re.I)


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "job-board-reader"})
        return json.load(urllib.request.urlopen(req, timeout=20))
    except Exception:
        return None


def read_company(slug):
    """Return every opening found for one company slug, in a common shape."""
    jobs = []
    data = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    for j in (data or {}).get("jobs", []):
        jobs.append({"company": slug, "source": "greenhouse", "title": j["title"],
                     "location": (j.get("location") or {}).get("name") or "",
                     "date": (j.get("updated_at") or "")[:10], "url": j["absolute_url"]})
    data = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    for j in data if isinstance(data, list) else []:
        cat = j.get("categories", {})
        places = [cat.get("location") or ""] + (cat.get("allLocations") or [])
        jobs.append({"company": slug, "source": "lever", "title": j["text"],
                     "location": "; ".join(dict.fromkeys(places)), "date": "", "url": j["hostedUrl"]})
    data = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    for j in (data or {}).get("jobs", []):
        places = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations", [])]
        jobs.append({"company": slug, "source": "ashby", "title": j["title"],
                     "location": "; ".join(places), "date": (j.get("publishedAt") or "")[:10],
                     "url": j["jobUrl"]})
    return jobs


def main(path):
    slugs = sorted({line.strip() for line in open(path) if line.strip() and not line.startswith("#")})
    with cf.ThreadPoolExecutor(16) as pool:
        results = list(pool.map(read_company, slugs))
    all_jobs = [job for jobs in results for job in jobs]
    found = sum(1 for jobs in results if jobs)
    shortlist = [j for j in all_jobs if LOCATION.search(j["location"]) and not EXCLUDE.search(j["title"])]

    json.dump(all_jobs, open("all_jobs.json", "w"), indent=1)
    with open("shortlist.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "title", "location", "date", "source", "url"])
        writer.writeheader()
        writer.writerows(sorted(shortlist, key=lambda j: (j["company"], j["title"])))
    print(f"{len(slugs)} companies · {found} with a public board · {len(all_jobs)} openings · "
          f"{len(shortlist)} in the shortlist")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "companies.txt")

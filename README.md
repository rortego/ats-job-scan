# Job-board scan

A small script that reads the public job boards of a list of companies and keeps the roles a candidate outside the US can actually apply to.

## The problem

"Remote" on a job board usually means remote within one country. Checking that by hand, company by company, takes hours. Many companies publish their openings through Greenhouse, Lever or Ashby, and all three expose a public, read-only JSON endpoint per company. Reading those endpoints directly gives the full list in seconds, with the real location field.

## What it does

1. Reads a list of company slugs from `companies.txt`.
2. Queries the three public endpoints for each one, in parallel.
3. Normalises the three formats into one shape: company, title, location, date, link.
4. Filters by location (which regions the role admits) and by title (which roles to leave out).
5. Writes `all_jobs.json` with everything it read and `shortlist.csv` with what passed.

No login, no scraping of pages, standard library only.

## Run it

```
python scan.py companies.txt
```

Example with the ten companies in the sample file:

```
10 companies · 10 with a public board · 2271 openings · 83 in the shortlist
```

## What I learned running it

I ran it against 157 companies: 17,827 openings, of which about 180 admitted a candidate in Argentina and were not engineering roles. The location filter is the valuable part. A plain "Remote" tag is ambiguous, so the shortlist is a starting point: I open each posting and read the eligibility paragraph before applying.

## Adapting it

Edit the two regular expressions at the top of `scan.py`: `LOCATION` for your region, `EXCLUDE` for the titles you do not want.

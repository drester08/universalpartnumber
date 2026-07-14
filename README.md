# UPN registry site

Static single-page site for `universalpartnumber.com`. No build step, client-side JavaScript, external font request, analytics, or cookies.

## Deploy

Import the repository into Vercel with **Framework Preset: Other** and leave the build command empty. The site is served directly from the repository root.

## Launch checklist requiring account access

- Configure `operators@universalpartnumber.com`, `manufacturers@universalpartnumber.com`, and `registry@universalpartnumber.com` as tested forwarding aliases.
- Attach `universalpartnumber.com` to the Vercel project.
- Register `universalpartnumber.org` and `universalpartnumber.net`, then configure permanent redirects to the `.com` domain.
- Supply approved Terms and Privacy destinations before launch; the footer paths are `/terms` and `/privacy`.
- Run the ownership-perception test in the build brief with someone unfamiliar with Filaway.

# Static site deployment

> This document is a deployment guide only. It does not create a Firebase project, authenticate to
> Firebase, upload files, change DNS, or deploy anything. No Firebase project is known to exist for
> this repository.

The site generator writes a provider-neutral static artifact to `public/`. Build and inspect that
artifact before using any hosting command:

```bash
python3 web/build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory public
```

Open `http://localhost:8000`, check the generated pages and links, and stop the local server with
Ctrl+C. Re-run the build after source changes. Treat `public/` as disposable generated output; do
not edit it in place.

## Why Firebase Hosting is the recommended default

[Firebase Hosting](https://firebase.google.com/docs/hosting) is a good fit for this site because the
output is static HTML, CSS, and other assets. Hosting provides managed HTTPS, CDN delivery,
temporary preview channels, release history, and optional custom domains without requiring an
application server. Preview channels make it practical to review a generated specification site
before changing its live channel.

This recommendation is operational convenience, not a JPS requirement or an endorsement embedded
in the specification. The `public/` artifact remains portable to other static hosting providers.

## One-time Firebase setup

The commands below use `jps-spec-preview-example` as an illustrative project ID. It is not known to
exist and is not reserved for this repository. Replace every occurrence with the exact ID of a
dedicated Firebase project that you are authorized to use.

1. Create or select a dedicated Firebase project in the Firebase console. A separate project
   reduces the chance that a documentation preview affects unrelated Firebase resources. For a
   strict no-billing preview, leave it on the Spark plan and do not attach a billing account.
2. Install or update the Firebase CLI using the
   [official CLI instructions](https://firebase.google.com/docs/cli). If the npm installation
   reports that the installed Node.js is unsupported, upgrade to a currently supported Node.js or
   use the official standalone Firebase CLI binary. Then verify the CLI, authenticate, and list the
   visible projects:

   ```bash
   firebase --version
   firebase login
   firebase projects:list
   ```

3. In the Firebase console, open **Hosting**, choose **Get started**, and provision the project's
   default classic Hosting site. Do not upload sample content. Then record the actual Hosting site
   ID returned by:

   ```bash
   firebase hosting:sites:list --project jps-spec-preview-example
   ```

   The default site ID is often the project ID, but do not assume they match. The clone example
   below uses `jps-spec-site-example` as a separate fictional site ID.
4. From the repository root, build the site and inspect `public/`. Confirm it contains no secrets,
   credentials, private drafts, internal URLs, customer data, or untracked files that should not be
   public.
5. Review the repository's existing `firebase.json`. It points classic Firebase Hosting at
   `public/`, enables clean static URLs, supplies conservative cache and security headers, and has
   no backend or single-page-app rewrite. Do not run `firebase init` over it during normal setup.
6. Either keep passing the exact `--project jps-spec-preview-example` argument shown below or copy
   `.firebaserc.example` to the ignored `.firebaserc` file and replace its placeholder with the
   verified project ID. A real project binding is deliberately not committed.

The [Firebase Hosting quickstart](https://firebase.google.com/docs/hosting/quickstart) is the source
of truth if the CLI prompts differ from this guide.

## Deploy a preview first

Rebuild from a clean, reviewed revision immediately before previewing:

```bash
python3 web/build.py
firebase hosting:channel:deploy spec-review --expires 7d --no-authorized-domains --project jps-spec-preview-example
```

Before confirming the command, verify the project ID shown by the CLI. This command is an external
write: it uploads the Hosting configuration and current `public/` contents to the `spec-review`
preview channel. `--no-authorized-domains` prevents this static documentation deployment from
changing Firebase Authentication's authorized-domain list. The returned preview URL is temporary
but public to anyone who has it; it is not an access-control boundary.

Review the preview URL on desktop and mobile, follow internal and external links, and compare the
displayed version with the intended source checkout. Normative `0.1.0-draft` artifacts and their
browsable views link to the immutable tag. Living overview, tooling, and boundary pages updated
after that tag link to the clearly labelled current `main` source instead; they must not be
presented as tagged content. A Firebase preview-channel URL is temporary and should be shared as a
deployment candidate, not as the durable specification URL. The explicit seven-day expiration
limits stale preview content; Firebase permits changing or deleting the channel sooner.

## Promote the reviewed preview to live

Obtain explicit release approval before changing the live channel. To publish the exact version
that reviewers saw, clone the preview channel to the live channel:

```bash
firebase hosting:clone jps-spec-site-example:spec-review jps-spec-site-example:live
```

Replace both fictional site IDs with the actual ID from `firebase hosting:sites:list`, then confirm
the source and target before approving the clone. This command changes the live site. Afterward,
verify the live `web.app` or `firebaseapp.com` URL reported by Firebase and repeat the critical page
and link checks.

If promotion by cloning is not appropriate, Firebase also supports a direct live deployment from
the repository root:

```bash
python3 web/build.py
firebase deploy --only hosting --project jps-spec-preview-example
```

A direct deployment should be exceptional in this workflow because rebuilding or changing local
files after preview review can introduce drift. Inspect `public/` again before running it. The
`--only hosting` scope prevents an accidental deployment of unrelated Firebase resource types.

See Firebase's guide to
[testing, previewing, and deploying](https://firebase.google.com/docs/hosting/test-preview-deploy)
for current channel behavior.

## Custom domain

First verify the Firebase-provided live URL. Then use the **Hosting** page in the Firebase console
to add a custom domain and follow the displayed ownership, DNS, and certificate steps exactly. Do
not copy DNS values from examples or from another project. Firebase Hosting provisions and renews
the TLS certificate after domain verification and DNS propagation.

Coordinate any production DNS cutover with the domain owner. Use the console's advanced migration
flow when an existing domain must remain available during a provider change. DNS and certificate
provisioning can take time, so keep the Firebase-provided URL available for verification. Refer to
the current [custom-domain guide](https://firebase.google.com/docs/hosting/custom-domain).

## Rollback and cleanup

For a live rollback, open the intended site's Hosting release history in the Firebase console,
identify a known-good previous version, and choose **Roll back**. Confirm the site and version; a
rollback creates a new live release pointing to the selected earlier content. Do not try to repair a
bad live release by editing generated files directly.

Delete a preview channel early when it is no longer needed:

```bash
firebase hosting:channel:delete spec-review --project jps-spec-preview-example
```

That command deactivates the preview URL and schedules its channel releases for cleanup. Verify the
project and channel name before confirming deletion. Preview channels with an expiration also clean
themselves up; the live channel does not expire and cannot be deleted as a preview channel.

Use the Firebase console to set release-retention limits or remove old, non-current releases when
storage cleanup is needed. Deleting a previous release removes recoverable content, so retain at
least one verified rollback candidate and confirm that a version is not needed by another channel.
The current details are in Firebase's
[channel and release management guide](https://firebase.google.com/docs/hosting/manage-hosting-resources).

## Cost and quota caveat

Firebase plans, prices, and quotas can change. As checked on 2026-07-22, the Firebase pricing page
lists a no-cost Hosting allowance of 10 GB stored and 360 MB/day transferred, including custom
domain and SSL support. This small static site should fit comfortably for ordinary preview traffic,
but that is an estimate rather than a spending guarantee. For a strict no-billing setup, remain on
the Spark plan without a billing account and accept that service can be interrupted if a no-cost
quota is exhausted. If the project is upgraded to Blaze to use credits, usage beyond no-cost quotas
can incur charges and credits are not a spending cap. Hosting usage is measured at the project
level, including all sites and channels in that project; preview releases consume storage too.
Review the current [Firebase pricing page](https://firebase.google.com/pricing) and
[Hosting usage, quota, and pricing documentation](https://firebase.google.com/docs/hosting/usage-quotas-pricing)
before creating a project or enabling billing. Monitor storage and data transfer, set sensible
release-retention limits, and configure budget alerts if billing is enabled. Budget alerts notify;
they do not cap charges.

## Provider-neutral alternative

Firebase is optional. After running `python3 web/build.py`, publish the contents of `public/` with
any static host that can serve an `index.html`, preserve paths and MIME types, and provide HTTPS.
Configure that provider's build output or upload root as `public/`; no Python process, server-side
rendering, database, or Firebase SDK is required at runtime.

Apply the same preview-before-live, public-content review, custom-domain, retention, cost, and
rollback precautions with whichever provider is selected.

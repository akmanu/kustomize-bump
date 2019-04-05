# kustomize-bump

This script allows you to bump the tag versions of all the Docker images defined in a `kustomization.yaml` file.

It does this by:
1. Parsing `kustomization.yaml`
2. Finding out the tags and images of each field in `images:`
3. Asking [docker-hub-rss](https://rss.p.theconnman.com) which tags were released when
4. Skip image tags without any digits (probably means unversioned) (See `KBUMP_NODIGITS` for configuration)
5. Skip image tags with `['unstable', 'latest', 'testing', 'arm64', 'arm32']` in the name (See `KBUMP_FORBIDDEN_WORDS` for configuration)
6. Trying to magically find a good one (compare tag slugs, give less importance to older tags)
7. Writing the new candidate to `kustomization.yaml`


## Usage

```
docker run -t -v $(pwd)/kustomization.yaml:/kustomization.yaml chauffer/kustomize-bump
```

### Configuration

Environment variables:
- `KBUMP_NODIGITS`: Set to `0` to not skip images without numbers.
- `KBUMP_FORBIDDEN_WORDS`: Set to a comma separated string of forbidden words.
- `KBUMP_FILEPATH`: Path to `kustomization.yaml`. Defaults to `/kustomization.yaml`.

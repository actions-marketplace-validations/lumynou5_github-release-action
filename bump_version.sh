#!/usr/bin/bash

temp=$(mktemp)

sed -e "
/## \[Unreleased\]/{
G;
a\
## [$1] - $(date -I)
}
/\[Unreleased\]:/a\
[$1]: https://github.com/lumynou5/github-release-action/releases/tag/v$1
s/v[[:digit:]]*\.[[:digit:]]*\.[[:digit:]]*\.\.\.develop/v$1...develop/
" CHANGELOG.md >$temp

cat $temp >CHANGELOG.md
rm $temp

from os import environ as env
import keepachangelog
from github import Github


class Data(dict):
    def __missing__(self, key):
        return f'{{{key}}}'


def xstr(s):
    return str(s) if s is not None else ''


def getLatestChange():
    changes = keepachangelog.to_raw_dict(env['INPUT_CHANGELOG'])
    return list(changes.values())[0]


github = Github(base_url=env['GITHUB_API_URL'],
                login_or_token=env['INPUT_TOKEN'])
repo = github.get_repo(env['GITHUB_REPOSITORY'])

change = getLatestChange()
data = Data({
    'version': xstr(change['metadata']['version']),
    'major': xstr(change['metadata']['semantic_version']['major']),
    'minor': xstr(change['metadata']['semantic_version']['minor']),
    'patch': xstr(change['metadata']['semantic_version']['patch']),
    'prerelease': xstr(change['metadata']['semantic_version']['prerelease']),
    'build': xstr(change['metadata']['semantic_version']['buildmetadata']),
    'release-date': xstr(change['metadata']['release_date']),
})

# Create release.
tag = env['INPUT_TAG-TEMPLATE'].format_map(data)
release = repo.create_git_release(
    tag,
    env['INPUT_NAME-TEMPLATE'].format_map(data),
    change['raw'],
    env['INPUT_IS-DRAFT'] == 'true',
    data['prerelease'] is not None,
    env['GITHUB_SHA'])

# Move major tag.
if env['INPUT_MAJOR-TAG-TEMPLATE'] != '' and data['major'] != 0:
    major_tag = env['INPUT_MAJOR-TAG-TEMPLATE'].format_map(data)
    major = repo.get_git_ref(f'tags/{major_tag}')
    if major.ref is not None:
        major.edit(env['GITHUB_SHA'])
    else:
        repo.create_git_ref(f'refs/tags/{major_tag}', env['GITHUB_SHA'])
else:
    major_tag = ''

# Move minor tag.
if env['INPUT_MINOR-TAG-TEMPLATE'] != '':
    minor_tag = env['INPUT_MINOR-TAG-TEMPLATE'].format_map(data)
    minor = repo.get_git_ref(f'tags/{minor_tag}')
    if minor.ref is not None:
        minor.edit(env['GITHUB_SHA'])
    else:
        repo.create_git_ref(f'refs/tags/{minor_tag}', env['GITHUB_SHA'])
else:
    minor_tag = ''

# Output.
data['tag'] = tag
data['major-tag'] = major_tag
data['minor-tag'] = minor_tag
data['html-url'] = release.html_url
data['upload-url'] = release.upload_url
with open(env['GITHUB_OUTPUT'], 'a') as out:
    for (key, val) in data.items():
        print(f'{key}={val}', file=out)

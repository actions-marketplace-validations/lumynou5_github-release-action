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
data['tag'] = env['INPUT_TAG-TEMPLATE'].format_map(data)
release = repo.create_git_release(
    data['tag'],
    env['INPUT_NAME-TEMPLATE'].format_map(data),
    change['raw'],
    env['INPUT_IS-DRAFT'] == 'true',
    data['prerelease'] is not None,
    env['GITHUB_SHA'])

# Move major tag.
if env['INPUT_MAJOR-TAG-TEMPLATE'] != '' and data['major'] != 0:
    data['major_tag'] = env['INPUT_MAJOR-TAG-TEMPLATE'].format_map(data)
    major = repo.get_git_ref(f'tags/{data["major_tag"]}')
    if major.ref is not None:
        major.edit(env['GITHUB_SHA'])
    else:
        repo.create_git_ref(f'refs/tags/{data["major_tag"]}', env['GITHUB_SHA'])
else:
    data['major_tag'] = ''

# Move minor tag.
if env['INPUT_MINOR-TAG-TEMPLATE'] != '':
    data['minor_tag'] = env['INPUT_MINOR-TAG-TEMPLATE'].format_map(data)
    minor = repo.get_git_ref(f'tags/{data["minor_tag"]}')
    if minor.ref is not None:
        minor.edit(env['GITHUB_SHA'])
    else:
        repo.create_git_ref(f'refs/tags/{data["minor_tag"]}', env['GITHUB_SHA'])
else:
    data['minor_tag'] = ''

# Output.
data['html-url'] = release.html_url
data['upload-url'] = release.upload_url
with open(env['GITHUB_OUTPUT'], 'a') as out:
    for (key, val) in data.items():
        print(f'{key}={val}', file=out)

from os import environ as env
import keepachangelog
from github import Auth, Github, UnknownObjectException


class Data(dict):
    def __missing__(self, key):
        return f'{{{key}}}'


def xstr(s):
    return str(s) if s is not None else ''


def getLatestChange():
    changes = keepachangelog.to_raw_dict(env['INPUT_CHANGELOG'])
    return list(changes.values())[0]


github = Github(
    base_url=env['GITHUB_API_URL'],
    auth=Auth.Token(env['INPUT_TOKEN'])
)
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
    'change': xstr(change['raw']),
})

# Create release.
data['tag'] = env['INPUT_TAG-TEMPLATE'].format_map(data)
release = repo.create_git_release(
    data['tag'],
    env['INPUT_NAME-TEMPLATE'].format_map(data),
    data['change'],
    env['INPUT_IS-DRAFT'] == 'true',
    data['prerelease'] is not None,
    target_commitish=env['GITHUB_SHA']
)

# Move major tag.
if env['INPUT_MAJOR-TAG-TEMPLATE'] != '' and data['major'] != 0:
    data['major_tag'] = env['INPUT_MAJOR-TAG-TEMPLATE'].format_map(data)
    try:
        major = repo.get_git_ref(f'tags/{data["major_tag"]}')
        major.edit(env['GITHUB_SHA'])
    except UnknownObjectException:
        repo.create_git_ref(f'refs/tags/{data['major_tag']}', env['GITHUB_SHA'])
else:
    data['major_tag'] = ''

# Move minor tag.
if env['INPUT_MINOR-TAG-TEMPLATE'] != '':
    data['minor_tag'] = env['INPUT_MINOR-TAG-TEMPLATE'].format_map(data)
    try:
        minor = repo.get_git_ref(f'tags/{data["minor_tag"]}')
        minor.edit(env['GITHUB_SHA'])
    except UnknownObjectException:
        repo.create_git_ref(f'refs/tags/{data["minor_tag"]}', env['GITHUB_SHA'])
else:
    data['minor_tag'] = ''

# Output.
data['html-url'] = release.html_url
data['upload-url'] = release.upload_url
with open(env['GITHUB_OUTPUT'], 'a') as out:
    for (key, val) in data.items():
        delimiter = 'EOF'
        while delimiter in val:
            delimiter *= 2
        print(f'{key}<<{delimiter}\n{val}\n{delimiter}', file=out)

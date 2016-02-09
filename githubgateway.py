from basegateway import APIGateway
import git
import re
import os
from datetime import datetime
from operator import itemgetter
import copy

def owner_and_repo():
  g = git.cmd.Git(os.getcwd())
  remotes = g.execute(['git','remote','-v'])
  match = re.search('github\.com(?::|\/)([\w\-]+)\/([\w\-]+)\.git \(fetch\)', remotes)
  owner = None
  repo = None
  if match is not None:
    owner = match.group(1).encode('ascii')
    repo = match.group(2).encode('ascii')

  return owner, repo

def current_branch():
  return str(git.Repo(os.getcwd()).active_branch)

def issue_number_from_branch():
  ret = None
  branch = current_branch()
  match = re.search('^(\d+)\-', branch)
  if match is not None:
    ret = int(match.group(1))
  return ret

class GithubAPIGateway(APIGateway):
  def __init__(self, token=os.environ.get('GITHUB_TOKEN')):
    APIGateway.__init__(self)
    self._owner, self._repo = owner_and_repo()
    self._cache = {}
    self._host_url = 'https://api.github.com'
    self._api = {
      'list_issues': {
        'path': '/orgs/{org}/issues',
        'method': 'GET'
      },
      'list_issue': {
        'path': '/repos/{owner}/{repo}/issues/{number}',
        'method': 'GET',
        'valid_status': [200, 404]
      },
      'list_labels': {
        'path': '/repos/{owner}/{repo}/labels',
        'method': 'GET',
        'valid_status': [200, 404]
      },
      'list_label': {
        'path': '/repos/{owner}/{repo}/label/{name}',
        'method': 'GET',
        'valid_status': [200, 404]
      },
      'add_labels_to_issue': {
        'path': '/repos/{owner}/{repo}/issues/{number}/labels',
        'method': 'POST',
        'valid_status': [200, 404]
      },
      'remove_label_from_issue': {
        'path': '/repos/{owner}/{repo}/issues/{number}/labels/{name}',
        'method': 'DELETE',
        'valid_status': [200, 404]
      },
      'remove_all_labels_from_issue': {
        'path': '/repos/{owner}/{repo}/issues/{number}/labels',
        'method': 'DELETE',
        'valid_status': [204, 404]
      },
      'user': {
        'path': '/user',
        'method': 'GET',
        'valid_status': [200]
      },
      'create_issue': {
        'path': '/repos/{owner}/{repo}/issues',
        'method': 'POST'
      },
      'create_pr': {
        'path': '/repos/{owner}/{repo}/pulls',
        'method': 'POST',
        'valid_status': [201]
      },
      'list_pr': {
        'path': '/repos/{owner}/{repo}/pulls',
        'method': 'GET',
        'valid_status': [200]
      },
      'list_pr_review_comments': {
        'path': '/repos/{owner}/{repo}/pulls/{number}/comments',
        'method': 'GET',
        'valid_status': [200]
      },
      'list_issue_comments': {
        'path': '/repos/{owner}/{repo}/issues/{number}/comments',
        'method': 'GET',
        'valid_status': [200]
      },
      'list_issue_labels': {
        'path': '/repos/{owner}/{repo}/issues/{number}/labels',
        'method': 'GET',
        'valid_status': [200, 404]
      },
      'list_pr_commits': {
        'path': '/repos/{owner}/{repo}/pulls/{number}/commits',
        'method': 'GET',
        'valid_status': [200]
      },
      'merge_pr': {
        'path': '/repos/{owner}/{repo}/pulls/{number}/merge',
        'method': 'PUT',
        'valid_status': [200]
      }
    }
    self._common_headers = {
      'Authorization': 'token {0}'.format(token)
    }
    self._common_params = {}

  def create_issue(self, title, self_assign=False, data={}):
    data.update({'title': title})
    if self_assign:
      data.update({'assignee': self.call('user')[0]['login']})
    return self.call('create_issue', owner=self._owner, repo=self._repo, data=data)[0]

  def get_open_pr(self):
    ret = self._cache.get('pr')
    if ret is not None:
      return ret

    branch = str(current_branch())
    prs = self.call('list_pr', owner=self._owner, repo=self._repo, data={
      'head': branch
    })[0]

    for pr in prs:
      if pr['head']['ref'] == branch:
        self._cache['pr'] = pr
        return pr

    return None

  def get_current_issue(self):
    ret = self._cache.get('issue')
    if ret is not None:
      return ret

    issue_number = issue_number_from_branch()
    ret = self.call('list_issue', owner=self._owner, repo=self._repo, number=issue_number)[0]

    self._cache['issue'] = ret
    return ret

  def get_pr_comments(self):
    ret = self._cache.get('pr_comments')
    if ret is not None:
      return ret

    pr = self.get_open_pr()
    ret = None
    if pr is not None:
      ret = self.call('list_issue_comments', owner=self._owner, repo=self._repo, number=pr['number'])[0]
    else:
      ret = []

    self._cache['pr_comments'] = ret
    return ret

  def get_pr_commits(self):
    ret = self._cache.get('pr_commits')
    if ret is not None:
      return ret

    pr = self.get_open_pr()
    if pr is not None:
      ret = self.call('list_pr_commits', owner=self._owner, repo=self._repo, number=pr['number'])[0]
    else:
      ret = []

    self._cache['pr_commits'] = ret
    return ret

  def merge_pr(self):
    pr = self.get_open_pr()
    if pr is not None:
      return self.call('merge_pr', owner=self._owner, repo=self._repo, number=pr['number'], data={})[0]
    else:
      return None

  def get_user(self):
    ret = self._cache.get('user')
    if ret is not None:
      return ret

    ret = self.call('user')[0]

    self._cache['user'] = ret
    return ret

  def get_pr_review_comments(self):
    ret = self._cache.get('pr_review_comments')
    if ret is not None:
      return ret

    pr = self.get_open_pr()
    if pr is not None:
      ret = self.call('list_pr_review_comments', owner=self._owner, repo=self._repo, number=pr['number'])[0]
    else:
      ret = []

    self._cache['pr_review_comments'] = ret
    return ret

  def get_pr_and_review_comments(self):
    review_comments = self.get_pr_review_comments()
    pr_comments = self.get_pr_comments()
    comments = {}
    for comment_original in (review_comments + pr_comments):
      comment = copy.deepcopy(comment_original)
      user = comment['user']['login']
      if comments.get(user) is None:
        comments[user] = []

      comment['updated_at_datetime'] = datetime.strptime(comment['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
      comments[user].append(comment)

    for user, comments_array in comments.iteritems():
      comments_array.sort(key=itemgetter('updated_at_datetime'))

    return comments

  def get_labels(self, issue_number=None):
    if issue_number:
      return self.call('list_issue_labels', owner=self._owner, repo=self._repo, number=issue_number)
    else:
      return self.call('list_labels', owner=self._owner, repo=self._repo)

  def labels_exist(self, labels):
    results, status = self.get_labels()
    existing_labels = [label['name'] for label in results]
    return set(labels) < set(existing_labels)

  def add_labels_to_issue(self, issue_number, data, force_label_creation):
    if force_label_creation or self.labels_exist(data):
      return self.call('add_labels_to_issue', owner=self._owner, repo=self._repo, number=issue_number, data=data)
    else:
      return { 'message' : 'One or more labels do not exist.' }, 404

  def remove_label_from_issue(self, issue_number, label, remove_all_labels):
    if remove_all_labels:
      return self.call('remove_all_labels_from_issue', owner=self._owner, repo=self._repo, number=issue_number)
    else:
      return self.call('remove_label_from_issue', owner=self._owner, repo=self._repo, number=issue_number, name=label)
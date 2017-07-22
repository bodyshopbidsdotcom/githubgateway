from basegateway import APIGateway
import os
from datetime import datetime
from operator import itemgetter
import copy

class GithubAPIGateway(APIGateway):
  def __init__(self, owner, repo, token=os.environ.get('GITHUB_TOKEN')):
    APIGateway.__init__(self)
    self._owner = owner
    self._repo = repo
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
      'list_statuses': {
        'path': '/repos/{owner}/{repo}/commits/{ref}/statuses',
        'method': 'GET',
        'valid_status': [200]
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
      'list_collaborators': {
        'path': '/repos/{owner}/{repo}/collaborators',
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
      'list_issues': {
        'path': '/repos/{owner}/{repo}/issues',
        'method': 'GET',
        'valid_status': [200]
      },
      'list_issue_comments': {
        'path': '/repos/{owner}/{repo}/issues/{number}/comments',
        'method': 'GET',
        'valid_status': [200]
      },
      'create_issue_comment': {
        'path': '/repos/{owner}/{repo}/issues/{number}/comments',
        'method': 'POST',
        'valid_status': [201]
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

  def open_issues_with_labels(self, labels):
    return self.call('list_issues', owner=self._owner, repo=self._repo, params={'state': 'open', 'labels': ','.join(labels)})[0]

  def create_issue(self, title, self_assign=False, data={}):
    data.update({'title': title})
    if self_assign:
      data.update({'assignee': self.call('user')[0]['login']})
    return self.call('create_issue', owner=self._owner, repo=self._repo, data=data)[0]

  def get_pr_from_branch(self, branch_name, state = 'open'):
    prs = self.call('list_pr', owner=self._owner, repo=self._repo, params={
      'head': '{0}:{1}'.format(self._owner, branch_name)
    })[0]

    return next(iter(prs or []), None)

  def get_open_prs(self):
    return self.call('list_pr', owner=self._owner, repo=self._repo, data={
      'state': 'open'
    })

  def get_open_pr(self, branch_name):
    ret = self._cache.get('pr')
    if ret is not None:
      return ret

    prs = self.call('list_pr', owner=self._owner, repo=self._repo, data={
      'head': branch_name
    })[0]

    for pr in prs:
      if pr['head']['ref'] == branch_name:
        self._cache['pr'] = pr
        return pr

    return None

  def get_statuses_for_sha(self, sha):
    return self.call('list_statuses', owner=self._owner, repo=self._repo, ref=sha)[0]

  def get_issue(self, issue_number):
    ret = self._cache.get('issue')
    if ret is not None:
      return ret

    ret = self.call('list_issue', owner=self._owner, repo=self._repo, number=issue_number)[0]

    self._cache['issue'] = ret
    return ret

  def get_pr_comments(self, branch_name):
    ret = self._cache.get('pr_comments')
    if ret is not None:
      return ret

    pr = self.get_open_pr(branch_name)
    ret = None
    if pr is not None:
      ret = self.call('list_issue_comments', owner=self._owner, repo=self._repo, number=pr['number'])[0]
    else:
      ret = []

    self._cache['pr_comments'] = ret
    return ret

  def create_comment(self, issue_number, comment):
    data = { 'body': comment }
    return self.call('create_issue_comment', owner=self._owner, repo=self._repo, number=issue_number, data=data)

  def get_pr_commits(self, branch_name):
    ret = self._cache.get('pr_commits')
    if ret is not None:
      return ret

    pr = self.get_open_pr(branch_name)
    if pr is not None:
      ret = self.call('list_pr_commits', owner=self._owner, repo=self._repo, number=pr['number'])[0]
    else:
      ret = []

    self._cache['pr_commits'] = ret
    return ret

  def merge_pr(self, branch_name):
    pr = self.get_open_pr(branch_name)
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

  def list_collaborators(self):
    return self.call('list_collaborators', owner=self._owner, repo=self._repo)[0]

  def list_collaborators_usernames(self):
    ret = set()
    for collaborator in self.list_collaborators():
      if collaborator.get('login') is not None:
        ret.add(collaborator['login'])

    return ret

  def get_pr_review_comments(self, branch_name):
    ret = self._cache.get('pr_review_comments')
    if ret is not None:
      return ret

    pr = self.get_open_pr(branch_name)
    if pr is not None:
      ret = self.call('list_pr_review_comments', owner=self._owner, repo=self._repo, number=pr['number'])[0]
    else:
      ret = []

    self._cache['pr_review_comments'] = ret
    return ret

  def get_pr_and_review_comments(self, branch_name):
    review_comments = self.get_pr_review_comments(branch_name)
    pr_comments = self.get_pr_comments(branch_name)
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
    return set(labels) <= set(existing_labels)

  def add_labels_to_issue(self, issue_number, data, force_label_creation=False):
    if force_label_creation or self.labels_exist(data):
      return self.call('add_labels_to_issue', owner=self._owner, repo=self._repo, number=issue_number, data=data)
    else:
      return { 'message' : 'One or more labels do not exist.' }, 404

  def remove_label_from_issue(self, issue_number, label, remove_all_labels=False):
    if remove_all_labels:
      return self.call('remove_all_labels_from_issue', owner=self._owner, repo=self._repo, number=issue_number)
    else:
      return self.call('remove_label_from_issue', owner=self._owner, repo=self._repo, number=issue_number, name=label)

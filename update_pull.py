from service.pull import GitHubConnector


if __name__ == '__main__':
    gc = GitHubConnector()
    gc.check_and_update_pull_request()

import argparse

from service.pull import GitHubConnector


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--p", help="pages(optional)", type=int, default=1)
    args = parser.parse_args()

    gc = GitHubConnector()
    gc.save_all_commits(args.p)
    gc.check_newest_hash()

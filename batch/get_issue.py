import argparse
from pprint import pprint

from service.pull import GitHubConnector


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--p", help="pages(optional)", type=int, default=1)
    parser.add_argument(
        "--s", help="since: YYYY-mm-ddTHH:MM:SSZ(optional)", default='')
    args = parser.parse_args()

    gc = GitHubConnector()
    result = gc.save_all_issues(args.p, args.s)
    pprint(result)

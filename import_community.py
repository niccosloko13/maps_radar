"""Usage: python import_community.py [--file path]. Auto-discovers the project TXT."""
import argparse,json
import server,community
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--file');a=p.parse_args();server.init_db();print(json.dumps(community.import_file(server,a.file),ensure_ascii=False,indent=2))

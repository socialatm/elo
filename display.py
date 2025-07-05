import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Ranks UFC fighters by the Elo-rating system")
parser.add_argument("-n", "--number", dest="N", type=int, default=15, help="Number of fighters to be displayed (default: %(default)s)")
args = parser.parse_args()

display = pd.read_csv('display.csv')
display = display.set_index('Fighter')
pd.options.display.float_format = '{:.0f}'.format

print(f"\nTop {args.N} fighters:")
print(display.head(args.N))
print(f"\n")
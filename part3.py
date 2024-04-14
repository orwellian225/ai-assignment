import sys

def sub1_main():
    pass

def sub2_main():
    pass

submission_id = 1
match submission_id:
    case 1:
        sub1_main()
    case 2:
        sub2_main()
    case _:
        print("No specified submission - please select a submission number", file=sys.stderr)
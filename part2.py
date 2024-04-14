import sys

def sub1_main():
    pass

def sub2_main():
    pass

def sub3_main():
    pass

def sub4_main():
    pass

submission_id = 1
match submission_id:
    case 1:
        sub1_main()
    case 2:
        sub2_main()
    case 3:
        sub3_main()
    case 4:
        sub4_main()
    case _:
        print("No specified submission - please select a submission number", file=sys.stderr)
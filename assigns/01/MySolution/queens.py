"""Python 3 translation of the ATS eight-queens program in queens.dats.

The helper functions follow the ATS code closely. `search` is an equivalent
loop because Python does not perform tail-call optimization.
"""

N = 8


def print_dots(i):
    if i > 0:
        print(". ", end="")
        print_dots(i - 1)


def print_row(i):
    print_dots(i)
    print("Q ", end="")
    print_dots(N - i - 1)
    print()


def print_board(bd):
    print_row(bd[0])
    print_row(bd[1])
    print_row(bd[2])
    print_row(bd[3])
    print_row(bd[4])
    print_row(bd[5])
    print_row(bd[6])
    print_row(bd[7])
    print()


def board_get(bd, i):
    if i == 0:
        return bd[0]
    elif i == 1:
        return bd[1]
    elif i == 2:
        return bd[2]
    elif i == 3:
        return bd[3]
    elif i == 4:
        return bd[4]
    elif i == 5:
        return bd[5]
    elif i == 6:
        return bd[6]
    elif i == 7:
        return bd[7]
    else:
        return -1  # ATS ~1


def board_set(bd, i, j):
    x0, x1, x2, x3, x4, x5, x6, x7 = bd
    if i == 0:
        x0 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 1:
        x1 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 2:
        x2 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 3:
        x3 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 4:
        x4 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 5:
        x5 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 6:
        x6 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    elif i == 7:
        x7 = j
        return (x0, x1, x2, x3, x4, x5, x6, x7)
    else:
        return bd


def safety_test1(i0, j0, i1, j1):
    return j0 != j1 and abs(i0 - i1) != abs(j0 - j1)


def safety_test2(i0, j0, bd, i):
    if i >= 0:
        if safety_test1(i0, j0, i, board_get(bd, i)):
            return safety_test2(i0, j0, bd, i - 1)
        else:
            return False
    else:
        return True


def search(bd, i, j, nsol, verbose=True, solutions=None):
    """Same DFS as the ATS version, written as a loop.

    ATS compiles the tail-recursive `search` into jumps. Python does not
    optimize tail calls, so a literal recursive translation hits
    RecursionError before finishing all 92 solutions.
    """
    while True:
        if j < N:
            test = safety_test2(i, j, bd, i - 1)
            if test:
                bd1 = board_set(bd, i, j)
                if i + 1 == N:
                    if verbose:
                        print("Solution #", nsol + 1, ":\n\n", sep="", end="")
                        print_board(bd1)
                    if solutions is not None:
                        solutions.append(bd1)
                    j = j + 1
                    nsol = nsol + 1
                else:
                    bd = bd1
                    i = i + 1
                    j = 0
            else:
                j = j + 1
        else:
            if i > 0:
                j = board_get(bd, i - 1) + 1
                i = i - 1
            else:
                return nsol


def main():
    print_board((0, 1, 2, 3, 4, 5, 6, 7))
    nsol = search((0, 0, 0, 0, 0, 0, 0, 0), 0, 0, 0)
    assert nsol == 92


if __name__ == "__main__":
    main()

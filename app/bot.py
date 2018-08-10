# coding=utf-8
# from app.utils import *
import app.utils as lg


def main():
    w = lg.worker()
    next(w)
    while True:
        r = lg.get_updates()
        lg.calculate(r)
        w.send(True)


if __name__ == '__main__':
    main()

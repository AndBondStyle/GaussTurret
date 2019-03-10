import argparse
import cv2
import os


def main(args):
    cap = cv2.VideoCapture(0)
    if args.width: cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height: cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not os.path.isdir(args.folder): os.mkdir(args.folder)
    print('ENTER to save, S+ENTER to skip, Q+ENTER to exit')

    index = 1
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            print('Frame read error - quitting')
            break

        inp = input('>>> ')
        if inp.lower() == 's': continue
        if inp.lower() == 'q': break

        cv2.imwrite(args.folder + '/' + str(index) + '.jpg', frame)
        index += 1

    print('Saved', index - 1, 'snapshots to', args.folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save snapshots from the camera')
    parser.add_argument('--folder', default='snapshots', help='Path to the save folder (default: snapshots)')
    parser.add_argument('--width', default=None, type=int, help='Frame width (px)')
    parser.add_argument('--height', default=None, type=int, help='Frame height (px)')
    args = parser.parse_args()
    main(args)

from glob import glob
import numpy as np
import argparse
import cv2


def main(args):
    img_names = glob(args.folder + '/' + '*.jpg')

    pattern_size = (9, 6)
    pattern_points = np.zeros((np.prod(pattern_size), 3), np.float32)
    pattern_points[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)
    pattern_points *= args.dimension

    obj_points = []
    img_points = []
    height, width = cv2.imread(img_names[0], cv2.IMREAD_GRAYSCALE).shape[:2]

    for filename in img_names:
        print('Processing %s... ' % filename, end='')
        image = cv2.imread(filename, 0)
        if image is None: print('FAIL: Read error'); continue
        if (width, height) != image.shape: print('FAIL: Size mismatch'); continue
        ok, corners = cv2.findChessboardCorners(image, pattern_size)
        if not ok: print('FAIL: Chessboard not found'); continue

        if ok:
            print('OK!')
            term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, args.dimension, 0.001)
            cv2.cornerSubPix(image, corners, (5, 5), (-1, -1), term)

        img_points.append(corners.reshape(-1, 2))
        obj_points.append(pattern_points)

    rms, matrix, dist_coefs, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, (width, height), None, None)
    
    print('\nCALIBRATION RESULTS:\n')
    print('RMS:', rms)
    print('Camera matrix:\n', matrix)
    print('Distortion coefficients:', dist_coefs.ravel())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get camera calibration coefficients')
    parser.add_argument('--folder', default='snapshots', help='Path to snapshots folder (default: snapshots)')
    parser.add_argument('--dimension', default=25.0, type=float, help='Cell side length (mm)')
    args = parser.parse_args()
    main(args)

#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Fragment input image || 入力画像をフラグメント化する
Fragment input image according to coordinates definition definied on VoTT and UWP-FormDef
after rectifing the image.

入力画像を傾き補正し、VoTTとフォーム定義用のUWPアプリケーションで
エクスポートされたJSONファイルに含まれるメタデータをもとに、フラグメント化する

"""

import os
import io
import uuid
import json
import datetime
import sys
import requests
import collections

import cv2
from azure.storage.blob import BlockBlobService, ContentSettings

def retrieve_single_image(input_img, APPLICATION_STORAGE_ACCOUNT_NAME, APPLICATION_STORAGE_ACCESS_KEY, \
                          APPLICATION_STORAGE_CONTAINER_NAME):
    """Retrieve an application image || 入力画像1枚を取り出す

    Args:
        input_img (list): input image (numpy.ndarray) || 入力画像（numpy.ndarray）
        APPLICATION_STORAGE_ACCOUNT_NAME (str): storage account name for application images || 取り出しストレージアカウント名
        APPLICATION_STORAGE_ACCESS_KEY (str): storage access key || 取り出しストレージアクセスキー
        APPLICATION_STORAGE_CONTAINER_NAME(str): container name || 取り出しコンテナ名

    Returns:
        cv2_img（numpy.ndarray): read an image with OpenCV || OpenCVで画像データを読み込む
        download_filename（str): file name i.e. download-[original file name] || ローカルに保存した入力画像のファイル名

    """
    # Connect to Azure Data Lake Storage Gen2 || Data Lake Storage Gen2 へ接続
    block_blob_service = BlockBlobService(account_name=APPLICATION_STORAGE_ACCOUNT_NAME, \
                                          account_key=APPLICATION_STORAGE_ACCESS_KEY)

    # Retrieve an application image from Azure blob container || Azure blob のコンテナから入力画像１枚を取り出す
    download_filename = "download-" + os.path.basename(input_img)
    block_blob_service.get_blob_to_path(APPLICATION_STORAGE_CONTAINER_NAME, input_img, download_filename)
    cv2_img = cv2.imread(download_filename)
    return cv2_img, download_filename


def find_outer_frame_angle(img):
    """Find rotated rectangle || 最大領域の輪郭の座標・幅・高さ・回転角を取得する

    Args:
        img (numpy.ndarray): input image || 入力画像

    Returns:
        rotated_rect (tuple): rotated rectangle (top-left corner(x,y), (width, height), angle of rotation) || 最大領域の輪郭の座標・幅・高さ・回転角

    """
    # Convert an image from BGR to gray scale with OpenCV || OpenCVでBGRからグレースケール化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]

    # Find contours
    contours1 = cv2.findContours(thresh, cv2.RETR_EXTERNAL, \
                                 cv2.CHAIN_APPROX_SIMPLE)[1] # OpenCV3: 3 return values, OpenCV4: 2 return values

    # Find contour of the largest area || 最大領域の面積取得
    area_lists = []
    for cnt1 in contours1:
        area_lists.append(cv2.contourArea(cnt1))
    max_area = max(area_lists)

    for cnt1 in contours1:
        # If area is not matching with the largest area of contour || 領域がしめる面積が最大領域の面積と一致しなければ、
        # The next step will be skipped and the loop continues. || それ以降の内容がスキップされて次のループへ進む
        if  cv2.contourArea(cnt1) != max_area:
            continue

        # list of contour of the largest area (numpy array of coordinates x,y) || 最大領域の輪郭の list（輪郭上の点の(x,y)座標のNumpyのarray）
        contours = cnt1
        # Find rotated rectangle || 最大領域の輪郭座標の座標・幅・高さ・回転角を取得
        # return values - top-left corner(x,y), (width, height), angle of rotation || 戻り値3つ (左上の点(x,y)，横と縦のサイズ(width, height)，回転角)
        rotated_rect = cv2.minAreaRect(contours)
        # Reference:
        # https://seinzumtode.hatenadiary.jp/entry/20171121/1511241157

    return rotated_rect


def find_outer_frame(img):
    """Find rotated rectangle || 最大領域の輪郭の左上座標・幅・高さを取得する

    Args:
        img (numpy.ndarray): input image || 入力画像

    Returns:
        app_x (int): top-left x coordinate of the largest area || 最大領域の左上X座標
        app_y (int): top-left y coordinate of the largest area || 最大領域の左上Y座標
        big_w (int): width of the largest area || 最大領域の幅
        big_h (int): height of the largest area || 最大領域の高さ

    """
    # Convert an image from BGR to gray scale with OpenCV || OpenCVでBGRからグレースケール化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]

    contours1 = cv2.findContours(thresh, cv2.RETR_EXTERNAL, \
                                 cv2.CHAIN_APPROX_SIMPLE)[1] # OpenCV3: 3 return values, OpenCV4: 2 return values

    # Find contour of the largest area || 最大領域の面積取得
    area_lists = []
    for cnt1 in contours1:
        area_lists.append(cv2.contourArea(cnt1))
    max_area = max(area_lists)

    for cnt1 in contours1:
        # If area is not matching with the largest area of contour || 領域がしめる面積が最大領域の面積と一致しなければ、
        # The next step will be skipped and the loop continues. || それ以降の内容がスキップされて次のループへ進む
        if  cv2.contourArea(cnt1) != max_area:
            continue

        # top-left x, y coordinates and width, height of the largest area || 最大領域の輪郭の左上座標・幅・高さの取得（x,y:外接矩形の左上の位置、w,h:横と縦のサイズ）
        app_x, app_y, big_w, big_h = cv2.boundingRect(cnt1)

    return app_x, app_y, big_w, big_h


def calculate_angle(rotated_rect):
    """Calcurate rotation angle of input image || 入力画像の歪みの回転角を計算する

    Args:
        rotated_rect (tuple): contour of the largest area - top-left corner(x,y), (width, height), angle of rotation || 最大領域の輪郭の座標・幅・高さ・回転角

    Returns:
        angle (float): rotation angle which should be rectify || 修正すべき回転角

    """
    angle = rotated_rect[2] + 90 #rotation angle

    if angle > 45:
        angle = angle-90

    return angle


def rectify_image(angle, img):
    """Rectify input image || 入力画像の歪みを補正する

    Args:
        angle (float): rotation angle which should be rectify || 修正すべき回転角
        img (numpy.ndarray): input image || 入力画像

    Returns:
        rectified_cv2_img (numpy.ndarray): output image which is rectified || 歪み補正後の出力画像

    """
    num_rows, num_cols = img.shape[:2]
    rotation_matrix = cv2.getRotationMatrix2D((num_cols/2, num_rows/2), angle, 1)
    rectified_cv2_img = cv2.warpAffine(img, rotation_matrix, \
                                      (num_cols, num_rows)) #color image with no image distortion (BGR) || OpenCVカラー歪み無し (BGR)

    return rectified_cv2_img


def cut_into_fragments(coords, skiplist, app_x, app_y, big_w, big_h, img):
    """入力画像をフラグメント化する

    Args:
        coords (list): tag name and coordinates data retrieved from json file || JSONファイルから取り出されたタグ名と座標データ
        skiplist (list): skip fields list || フラグメント化除外リスト
        app_x (int): top-left x coordinate of the largest area || 最大領域の左上X座標
        app_y (int): top-left y coordinate of the largest area || 最大領域の左上Y座標
        big_w (int): width of the largest area || 最大領域の幅
        big_h (int): height of the largest area || 最大領域の高さ
        img (numpy.ndarray): input image || 入力画像

    Returns:
        field_imgs_printedjp (list): list of printed-Japanese fragment images || フラグメント画像（フラグメント化除外項目以外）のリスト（numpy.ndarray）
        field_imgs_digits (list): list of digits fragment images || フラグメント画像（フラグメント化除外項目以外）のリスト（numpy.ndarray）
        fieldName_printedjp (list): list of printed-Japanese field tag names || フィールド（フラグメント化除外項目以外）のタグ名リスト
        fieldName_digits (list): list of digits field tag names || フィールド（フラグメント化除外項目以外）のタグ名リスト

    """
    #Test3: This method
    for coord in coords:
        if coord[0] == 'LargestArea':
            adj_width=big_w/(coord[3]-coord[1])
            adj_height=big_h/(coord[8]-coord[2])
            x_top_left_out = coord[1]
            y_top_left_out = coord[2]

    print("adj_width: {}".format(adj_width))
    print("adj_height: {}".format(adj_height))
    print("x_top_left_out: {}".format(x_top_left_out))
    print("y_top_left_out: {}".format(y_top_left_out))
    print("app_x: {}".format(app_x))
    print("app_y: {}".format(app_y))

    field_imgs_printedjp = []
    field_imgs_digits = []
    fieldName_printedjp = []
    fieldName_digits = []
    for coord in coords:
        # フラグメント化除外項目以外をフラグメント化
        if (coord[0] == 'PrintedJP'):
            field_imgs_printedjp.append(img[round(app_y+(coord[2]-y_top_left_out)*adj_height):round(app_y+(coord[8]-y_top_left_out)*adj_height),round(app_x+(coord[1]-x_top_left_out)*adj_width):round(app_x+(coord[3]-x_top_left_out)*adj_width)])
            fieldName_printedjp.append(coord[0])
        if (coord[0] == 'Digits'):
            field_imgs_digits.append(img[round(app_y+(coord[2]-y_top_left_out)*adj_height):round(app_y+(coord[8]-y_top_left_out)*adj_height),round(app_x+(coord[1]-x_top_left_out)*adj_width):round(app_x+(coord[3]-x_top_left_out)*adj_width)])
            fieldName_digits.append(coord[0])

    print(len(coords))
    print(len(field_imgs_printedjp))
    print("fieldNamePrintedJP: {}".format(fieldName_printedjp))
    print(len(field_imgs_digits))
    print("fieldNameDigits: {}".format(fieldName_digits))
    return field_imgs_printedjp, field_imgs_digits, fieldName_printedjp, fieldName_digits


def save_fragments(field_imgs, FRAGMENT_STORAGE_ACCOUNT_NAME, FRAGMENT_STORAGE_ACCESS_KEY, \
                    FRAGMENT_STORAGE_CONTAINER_NAME, log_path, fragment_size, _ex_flag):
    """Save fragment images || フラグメント画像を保存する

    Args:
        field_imgs (list): list of fragment images || フラグメント画像のリスト（numpy.ndarray）
        FRAGMENT_STORAGE_ACCOUNT_NAME (str): storage account name for fragment images || フラグメント用 ストレージアカウント名
        FRAGMENT_STORAGE_ACCESS_KEY (str): storage access key || フラグメント用 ストレージアクセスキー
        FRAGMENT_STORAGE_CONTAINER_NAME(str): container name || フラグメント用 コンテナ名
        log_path（str): output destination of log file || ログファイル出力先
        fragment_size（int): bytes of transfered fragment image || フラグメント画像の転送バイト数
        _ex_flag（bool): error flag || エラー発生フラグ

    Returns:
        Save all fragment images (JPEG) to Azure Data Lake Storage Gen2 || JPEG形式の全フラグメント画像が指定保存先フォルダ（Azure Data Lake Storage Gen2）に保存される
        fragmentId (list): list of fragment images (GUID) || フラグメント画像につけられたGUID のリスト
        fragmentFilename (list): list of file names with extention || フラグメント画像の拡張子を含むファイル名のリスト
        blob_list（list): list of file name registered in blob || azure.storage.blobのコンテナーへ登録されたファイル名のリスト

    """
    # Connect to Azure Data Lake Storage Gen2 || Data Lake Storage Gen2 へ接続
    block_blob_service = BlockBlobService(account_name=FRAGMENT_STORAGE_ACCOUNT_NAME, \
                                            account_key=FRAGMENT_STORAGE_ACCESS_KEY)
    fragmentId = []
    fragmentFilename = []
    blob_list = []

    for i in range(len(field_imgs)):
        fragmentId.append(str(uuid.uuid4()))
        fragmentFilename.append(fragmentId[i] + ".jpg")

        # Encode || エンコード
        field_img_bytes = cv2.imencode('.jpg', field_imgs[i])[1].tobytes()
        stream = io.BytesIO(field_img_bytes)

        try:
            # Save fragment images to blob container || azure.storage.blobのコンテナへフラグメント化画像ファイルを保存
            block_blob_service.create_blob_from_stream(FRAGMENT_STORAGE_CONTAINER_NAME, fragmentFilename[i], stream, \
                    content_settings=ContentSettings(content_type='image/jpeg'), \
                    progress_callback=generate_progress_callback(fragmentFilename[i], fragment_size, _ex_flag))
        except Exception as ex: # pylint: disable=broad-except
            # If errors occour they are output in log file || エラーが発生した場合、ログファイルへ出力
            genarate_logger(FRAGMENT_STORAGE_ACCOUNT_NAME + ": When saved to " + FRAGMENT_STORAGE_CONTAINER_NAME + ", errors occoured. (save_fragments):" + str(ex), log_path)
            _ex_flag = False
            sys.exit(1)

        else:
            # Get object size in blob || blobの中のオブジェクトサイズを取得
            length = BlockBlobService.get_blob_properties(block_blob_service, \
                FRAGMENT_STORAGE_CONTAINER_NAME, fragmentFilename[i]).properties.content_length
            # If object size is different from transfered size it is  output in log file || 転送するサイズと転送後のサイズが違う場合、ログファイルへ出力
            if length != (int(fragment_size[1])):
                genarate_logger(FRAGMENT_STORAGE_ACCOUNT_NAME + ":" + FRAGMENT_STORAGE_CONTAINER_NAME + " is not saved correctly. The bytes of transfered fragment image is diffrent from actual size.(save_fragments):" \
                    + fragmentFilename[i] + " Bytes of transfered fragment image ：" + str(fragment_size[1]) + ": Actual size in blob :" + str(length), log_path)
                _ex_flag = False
                sys.exit(1)
            else:
                blob_list.append(fragmentId[i])

    return fragmentId, fragmentFilename, blob_list


def check_fragment_count(blob_list, fragmentId, log_path, _fragment_count_flag):
    """Count fragment images || フラグメント画像の枚数確認

    Args:
        blob_list（list): list of file name registered in blob || azure.storage.blobのコンテナーへ登録されたファイル名のリスト
        fragmentId (list): list of fragment images (GUID) || フラグメント画像につけられたGUID のリスト
        log_path（str): output destination of log file || ログファイル出力先
        _fragment_count_flag（bool): error flag || エラー発生フラグ

    """

    # If the number of fragment images is different from the number of images saved to blob || フラグメント画像件数とazure.storage.blobコンテナへのファイル保存の件数が違う時
    if len(fragmentId) != len(blob_list):
        for i in range(len(fragmentId)):
            for j in blob_list:
                if (fragmentId[i]) == j:
                    break
            else:
                # Output error logs || エラーログ出力
                genarate_logger(fragmentId[i] + ".jpg : Not being saved in azure.storage.blob. (check_fragment_count)", log_path)
                _fragment_count_flag = False


def generate_progress_callback(blob_name, fragment_size, _ex_flag):
    """Get the amount of transferred bytes || アップロード済みの画像容量（バイト数）の取得

    Args:
        blob_name（str): file name with extention || フラグメント画像の拡張子を含むファイル名
        fragment_size（int): the amount of current transfered bytes || progress_callbackで取得したcurrent（現在のアップロード済みのバイト数）
        _ex_flag（bool): error flag || エラー発生フラグ

    Returns:
        progress_callback (str): file name of fragment image, the amount of current transfered bytes, the amount of total bytes || フラグメント画像名、現在のアップロード済みのバイト数、フラグメント画像の総バイト数

    """
    try:
        def progress_callback(current, _total):
            fragment_size.clear()
            fragment_size.append(blob_name)
            fragment_size.append(current)
    except Exception as ex: # pylint: disable=broad-except
        # If errors occour they are output in log file || エラーが発生した場合、ログファイルへ出力
        genarate_logger("When saved to azure.storage.blob, errors occoured. (generate_progress_callback):" + str(ex), log_path)
        _ex_flag = False
        sys.exit(1)
    finally:
        pass

    return progress_callback


def genarate_logger(error_message, log_path):
    """Output error log || エラーログ出力

    Args:
        error_message(str):error messages || エラーメッセージ内容
        log_path(str): output destination of error messages || エラーメッセージ出力先

    Returns:
        Output error log
    """

    # Check if output destination is exist || ログファイル出力先フォルダを確認
    if not os.path.exists(os.path.join(log_path)):
        os.makedirs(os.path.join(log_path))

    # Get current date and time || 日時取得
    now = datetime.datetime.now()
    # Set file name || ファイル名設定
    file_name = 'f_' + now.strftime('%Y%m%d') + '.log'
    # Open the file || ファイルをオープン
    with open(os.path.join(log_path, file_name), mode='a', encoding='utf-8') as log_file:
    # Output logs || ログを出力
        log_file.write('******************************' + '\r')
        log_file.write(now.strftime('%Y-%m-%d %H:%M:%S') + '\r')
        log_file.write(error_message + '\r')


def get_json(vott_json_path):
    """Open VoTT json file || JSONファイルを開く

    Args:
        vott_json_path (str): VoTT json file path || VoTT json ファイル保存パス

    Returns:
        conf(file): json file || JSONファイル

    """

    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    # Open json file || JSONファイルを開く
    with open(vott_json_path,"r",encoding="utf-8_sig")as j_file:
        conf = decoder.decode(j_file.read())
    return conf


def get_coords(conf, lastVisitedAssetId):
    """Get tag name and coordinates data from json file || JSONファイルからタグ名と座標データを取得する

    Args:
        conf(file): json file || JSONファイル
        lastVisitedAssetId (str): last visited asset id from VoTT json file

    Returns:
        coords_list (list): tag name and coordinates data from json file || JSONファイルから取り出されたタグ名と座標データ
        firldTg, x_top_left, y_top_left, x_top_right, y_top_right, x_bottom_right, y_bottom_right, x_bottom_left, y_bottom_left

    """

    for j_key in conf:

        if j_key == 'assets':

            ct = 0
            l_ct = len(conf["assets"][lastVisitedAssetId]["regions"])

            coords_list = [[0 for column in range(9)] for row in range(l_ct)]
            r_ct = 0

            # Insert tag name and coordinates data into list
            for c_row in range(l_ct):
                p_ct = 0
                for c_col in range(9):
                    # tag name
                    if r_ct == 0:
                        coords_list[c_row][c_col] = conf["assets"][lastVisitedAssetId]["regions"][ct]["tags"][0]
                        r_ct += 1
                    # x-coordinate
                    elif r_ct == 1:
                        coords_list[c_row][c_col] = conf["assets"][lastVisitedAssetId]["regions"][ct]["points"][p_ct]["x"]
                        r_ct += 1
                    # y-coordinate
                    else:
                        coords_list[c_row][c_col] = conf["assets"][lastVisitedAssetId]["regions"][ct]["points"][p_ct]["y"]
                        p_ct += 1
                        r_ct = 1

                p_ct += 1
                r_ct = 0
                ct += 1

    return coords_list


input_img = sys.argv[1]
log_path = '../test/adls_log'
vott_json_path = 'YOUR_VOTT_JSON_PATH'
lastVisitedAssetId ='YOUR_LAST_VISITED_ASSET_ID'
skiplist = ["LargestArea"]

# Azure Data Lake Storage Gen2 connection || Azure Data Lake Storage Gen2 接続内容
FRAGMENT_STORAGE_ACCOUNT_NAME = 'YOUR_FRAGMENT_STORAGE_ACCOUNT_NAME'
FRAGMENT_STORAGE_ACCESS_KEY = 'YOUR_FRAGMENT_STORAGE_ACCESS_KEY'
FRAGMENT_STORAGE_CONTAINER_NAME_DIGITS = 'YOUR_FRAGMENT_STORAGE_CONTAINER_NAME_DIGITS'
FRAGMENT_STORAGE_CONTAINER_NAME_PRINTEDJP = 'YOUR_FRAGMENT_STORAGE_CONTAINER_NAME_PRINTEDJP'

# Azure Data Lake Storage Gen2 connection || Azure Data Lake Storage Gen2 接続内容
APPLICATION_STORAGE_ACCOUNT_NAME = 'YOUR_APPLICATION_STORAGE_ACCOUNT_NAME'
APPLICATION_STORAGE_ACCESS_KEY = 'YOUR_APPLICATION_STORAGE_ACCESS_KEY'
APPLICATION_STORAGE_CONTAINER_NAME = 'YOUR_APPLICATION_STORAGE_CONTAINER_NAME'

fragment_size = []
_ex_flag = True # error flag || Errorがあるかないか
_fragment_count_flag = True # fragment images count flag || フラグメントの数があってるか


def main():
    """Create and save fragment images, and send messages according to the coordinate definitions || アプリケーション画像を座標定義に従ってフラグメント画像を作成・保存・メッセージの送信をおこなう

    """
    original_cv2_img, download_filename = retrieve_single_image(input_img, APPLICATION_STORAGE_ACCOUNT_NAME, APPLICATION_STORAGE_ACCESS_KEY, \
                                             APPLICATION_STORAGE_CONTAINER_NAME)
    rotated_rect = find_outer_frame_angle(original_cv2_img)

    angle = calculate_angle(rotated_rect)
    rectified_cv2_img = rectify_image(angle, original_cv2_img)

    app_x_after, app_y_after, big_w_after, big_h_after = find_outer_frame(rectified_cv2_img)

    conf = get_json(vott_json_path)
    coords = get_coords(conf, lastVisitedAssetId)

    field_imgs_printedjp, field_imgs_digits, fieldName_printedjp, fieldName_digits = cut_into_fragments(coords, skiplist, app_x_after, app_y_after, big_w_after, big_h_after, rectified_cv2_img)

    fragmentId_p, fragmentFilename_p, blob_list_p = save_fragments(field_imgs_printedjp, FRAGMENT_STORAGE_ACCOUNT_NAME, FRAGMENT_STORAGE_ACCESS_KEY, FRAGMENT_STORAGE_CONTAINER_NAME_PRINTEDJP, log_path, fragment_size, _ex_flag)
    fragmentId, fragmentFilename, blob_list = save_fragments(field_imgs_digits, FRAGMENT_STORAGE_ACCOUNT_NAME, FRAGMENT_STORAGE_ACCESS_KEY, FRAGMENT_STORAGE_CONTAINER_NAME_DIGITS, log_path, fragment_size, _ex_flag)

if __name__ == '__main__':
    main()

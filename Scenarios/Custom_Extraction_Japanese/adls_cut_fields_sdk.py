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

import cv2
from azure.storage.blob import BlockBlobService, ContentSettings
import msal

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
                                 cv2.CHAIN_APPROX_SIMPLE)[0] # OpenCV3: 3 return values, OpenCV4: 2 return values

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
                                 cv2.CHAIN_APPROX_SIMPLE)[0] # OpenCV3: 3 return values, OpenCV4: 2 return values

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


def generate_application_info(input_img, APPLICATION_STORAGE_CONTAINER_NAME):
    """Get form type, Generate id and file name form storage path of input image || フォーム入力画像のパスからフォームタイプを取得とID・ファイル名の生成

    Args:
        input_img (str): storage path of input image || 入力画像のパス
        APPLICATION_STORAGE_CONTAINER_NAME(str): container name for application images || 取り出しコンテナ名

    Returns:
        applicationId (str): file name for input image (GUID) || フォーム入力画像につけられたGUID
        storagePath (str): storage path || ストレージパス
        applicationFileName (str): file name for input image (GUID) with extention || 拡張子を含むフォーム入力画像のファイル名

    """
    applicationId = str(uuid.uuid4())
    storagePath = APPLICATION_STORAGE_CONTAINER_NAME + '/' + os.path.basename(os.path.dirname(input_img)) # Will get through API
    applicationFileName = os.path.basename(input_img)

    return applicationId, storagePath, applicationFileName


def cut_into_fragments(coords, app_x, app_y, big_w, big_h, img, formExtent):
    """Fragment input image || 入力画像をフラグメント化する

    Args:
        coords (list): tag name and coordinates data retrieved from json file || JSONファイルから取り出されたタグ名と座標データ
        app_x (int): top-left x coordinate of the largest area || 最大領域の左上X座標
        app_y (int): top-left y coordinate of the largest area || 最大領域の左上Y座標
        big_w (int): width of the largest area || 最大領域の幅
        big_h (int): height of the largest area || 最大領域の高さ
        img (numpy.ndarray): input image || 入力画像
        formExtent（list): formExtent retrieved from json file || JSONファイルから取り出されたformExtent（外枠）

    Returns:
        field_imgs (list): list of fragment images || フラグメント画像のリスト（numpy.ndarray）
        fieldName (list): list of field tag names || フィールドのタグ名リスト

    """

    adj_width = big_w/(formExtent[0])
    adj_height = big_h/(formExtent[1])

    field_imgs = []
    fieldName = []
    for coord in coords:

        field_imgs.append(img[round(app_y+(coord[2])*adj_height): \
                            round(app_y+(coord[4])*adj_height), \
                            round(app_x+(coord[1])*adj_width): \
                            round(app_x+(coord[3])*adj_width)])
        fieldName.append(coord[0])

    return field_imgs, fieldName


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


def generate_fragment_info(field_imgs, applicationId, fragmentId, fieldName, fragmentFilename):
    """Generate list of fragment images data || フラグメントデータのリスト生成

    Args:
        field_imgs (list): list of fragment images || フラグメント画像のリスト（numpy.ndarray）
        applicationId (str): GUID for application image || フォーム入力画像につけられたGUID
        fragmentId (list): list of GUID for fragment images || フラグメント画像につけられたGUID のリスト
        fieldName (list): list of field tags || フィールドのタグ名リスト
        fragmentFilename (list): list of file name (fragment images) with extention || フラグメント画像の拡張子を含むファイル名のリスト

    Returns:
        fragment_info (list): list of fragment images data || フラグメントデータのリスト

    """
    _fragment_info = []
    for i in range(len(field_imgs)):
        _fragment_info.append([applicationId, fragmentId[i], fieldName[i], fragmentFilename[i]])

    return _fragment_info


def get_json_API(storage_path, log_path, API_ENDPOINT_URI, token):
    """Get json file through API || APIからJSONファイルを取得する

    Args:
        storage_path (str): storage path || ストレージパス
        log_path（str): output destination of log file || ログファイル出力先

    Returns:
        conf(file):json file || JSONファイル

    """

    http_header = {
        "accept": "application/json", 'Authorization': 'Bearer ' + token
    }
    url = API_ENDPOINT_URI + 'api/Form?path=' + storage_path
    try:
        response = requests.get(url, headers=http_header)

        if response.status_code == 200:
            # Get json file || JSONファイル取得
            response_json = response.text
            conf = json.loads(response_json)
        else:
            genarate_logger("Fail in API_Form_GET : response.status_code :" + str(response.status_code), log_path)
    except requests.exceptions.RequestException as e:
        genarate_logger("Fail in API_Form_GET :" + str(e), log_path)

    return conf


def get_coords(conf):
    """APIで取得したJSONファイルからタグ名、座標、formID、fieldName、fieldType、fieldOptionsを取得しリストを作成する。

    Args:
        conf(file): json file || JSONファイル

    Returns:
        coords_list (list): tag name and coordinates data from json file || JSONファイルから取り出されたタグ名と座標データ（fieldName,top_left_x,topleft_y,topleft_x+width,topleft_y+height)
        formId（str): formID from json file || JSONファイルから取り出されたformID
        fieldName（list): tag name from json file || JSONファイルから取り出されたタグ名
        fieldType（list): fieldType from json file || JSONファイルから取り出されたfieldType
        fieldOptions（list): fieldOptions from json file || JSONファイルから取り出されたfieldOptions
        formExtent（list): formExtent from json file || JSONファイルから取り出されたformExtent（外枠）

    """

    formExtent = []
    fieldName = []
    fieldType = []
    fieldOptions = []

    # Get key || キーを取得
    for json_key in conf:
        if json_key == 'formId':
            # Get formId || JSONファイルのキーがformIdを取得
            formId = conf["formId"]
        elif json_key == 'formExtent':
            # Get width and height of formExtent || キーのformExtent（外枠）のwidth、heightを取得
            formExtent.append(conf["formExtent"]["width"])
            formExtent.append(conf["formExtent"]["height"])
        elif json_key == 'fields':
            # Get tags and coordinates of fields || キーがfieldsの時タグ名、座標を取得
            tags_ct = 0
            element_ct = 0
            # Empty list for tags and coordinates || タグ名、座標を格納する配列
            coords_list = []

            # Get number of tags || タグ数取得
            tags_ct = len(conf["fields"])

            # Store coodinates to the list || 配列へ座標を格納する
            for _coords_ct in range(tags_ct):
                element_list = []

                # tag
                element_list.append(conf["fields"][element_ct]["fieldName"])
                # topleft_x
                element_list.append(conf["fields"][element_ct]["coordinate"]["topLeft"]["x"])
                # topleft_y
                element_list.append(conf["fields"][element_ct]["coordinate"]["topLeft"]["y"])
                # topleft_x + width
                element_list.append(conf["fields"][element_ct]["coordinate"]["topLeft"]["x"] + conf["fields"][element_ct]["coordinate"]["heightWidth"]["width"])
                # topleft_y + height
                element_list.append(conf["fields"][element_ct]["coordinate"]["topLeft"]["y"] + conf["fields"][element_ct]["coordinate"]["heightWidth"]["height"])
                coords_list.append(element_list)
                fieldName.append(conf["fields"][element_ct]["fieldName"])
                fieldType.append(conf["fields"][element_ct]["fieldType"])
                fieldOptions.append(conf["fields"][element_ct]["fieldOptions"])
                element_ct += 1

    return coords_list, formId, fieldName, fieldType, fieldOptions, formExtent


def put_processed_img(input_img, download_filename, APPLICATION_STORAGE_ACCOUNT_NAME, APPLICATION_STORAGE_ACCESS_KEY, PROCESSED_STORAGE_ACCOUNT_NAME, PROCESSED_STORAGE_ACCESS_KEY, PROCESSED_STORAGE_CONTAINER_NAME, AZ_BATCH_JOB_ID):
    """Transfer application image into another blob after processed || フラグメント化が完了した画像ファイルをADLSの作業終了用フォルダへ移動させる

    Args:
        input_img (str): storage path of input image || 入力画像のパス
        download_filename（str): file name saved locally || ローカルに保存した入力画像のファイル名
        APPLICATION_STORAGE_ACCOUNT_NAME (str): storage account name for application image || 取り出しストレージアカウント名
        APPLICATION_STORAGE_ACCESS_KEY (str): storage access key for application image || 取り出しストレージアクセスキー
        PROCESSED_STORAGE_ACCOUNT_NAME (str): storage account name for processed application image || 作業終了用 ストレージアカウント名
        PROCESSED_STORAGE_ACCESS_KEY (str): storage access jet for processed application image || 作業終了用 ストレージアクセスキー
        PROCESSED_STORAGE_CONTAINER_NAME(str): container name for processed application image || 作業終了用 コンテナ名
        AZ_BATCH_JOB_ID（str): JOB_ID which is created on Azure Batch || Azure Bacthで作成されたJOB_ID

    Returns:
        Transfer application image into another blob after processed || フラグメント化が完了した画像ファイルをADLSの作業終了用フォルダへ移動させる
    """

    job_id = AZ_BATCH_JOB_ID

    try:
        # Connect to Azure Data Lake Storage Gen2 (blob for processed images) || Data Lake Storage Gen2 へ接続 (blob for processed images)
        block_blob_service_P = BlockBlobService(account_name=PROCESSED_STORAGE_ACCOUNT_NAME, \
                                                account_key=PROCESSED_STORAGE_ACCESS_KEY)
        # input_img（フォルダ/ファイル名）でコンテナへ保存
        # Copy the image to ADLS processed folder || Azure Data Lake Storage Gen2 の processed コンテナへ画像をコピー
        block_blob_service_P.create_blob_from_path(PROCESSED_STORAGE_CONTAINER_NAME, job_id + '\\' + APPLICATION_STORAGE_CONTAINER_NAME + '\\' + os.path.dirname(input_img) + '\\' + os.path.basename(input_img), download_filename)
    except Exception as ex: # pylint: disable=broad-except
        # If errors occour they are output in log file || エラーが発生した場合、ログファイルへ出力
        genarate_logger(PROCESSED_STORAGE_ACCOUNT_NAME + ": When " + download_filename + " is saved to " + PROCESSED_STORAGE_CONTAINER_NAME + ", errors occoured. (put_processed_img):" + str(ex), log_path)
        _ex_flag = False
        sys.exit(1)

    try:
        # Azure Data Lake Storage Gen2 dlsdessdev002 へ接続(healthcheck)
        block_blob_service_A = BlockBlobService(account_name=APPLICATION_STORAGE_ACCOUNT_NAME, \
                                                account_key=APPLICATION_STORAGE_ACCESS_KEY)
        # Azure Data Lake Storage Gen2 dlsdessdev002 のhealthcheckコンテナの入力画像を削除する
        block_blob_service_A.delete_blob(APPLICATION_STORAGE_CONTAINER_NAME, input_img)
    except Exception as ex: # pylint: disable=broad-except
        # If errors occour they are output in log file || エラーが発生した場合、ログファイルへ出力
        genarate_logger(APPLICATION_STORAGE_ACCOUNT_NAME + ": When " + input_img + " is deleted from "+ APPLICATION_STORAGE_CONTAINER_NAME + ", errors occoured. (put_processed_img):" + str(ex), log_path)
        _ex_flag = False
        sys.exit(1)


def put_application(applicationId, formId, applicationFileName, API_ENDPOINT_URI, token):
    """Save data to CosmosDB (Applications table) through API || APIを介してCosmosDBのApplications テーブルへデータ (ApplicationId, FormId, ApplicationFileName)を保存する

    Args:
        applicationId (str): GUID for application image || フォーム入力画像につけられたGUID
        formId（str):GUID which is generated on UWP-FormDef || GUID, UWP-FormDefで定義時につけられるID
        applicationFileName (str): file name of application image with extention || 拡張子を含むフォーム入力画像のファイル名
    Returns:
        response（response): HTTP status code || HTTPステータスコード

    """

    http_header = {
        "accept": "application/json", 'Authorization': 'Bearer ' + token, "Content-Type": "application/json-patch+json"
    }

    http_data = {
        "applicationId":applicationId,
        "formId":formId,
        "applicationFileName":applicationFileName
    }

    #http communication || http通信
    url = API_ENDPOINT_URI + "api/Application/%s" % (applicationId)

    try:
        response = requests.put(url, data=json.dumps(http_data), headers=http_header)
        return response
    except requests.exceptions.RequestException:
        return False


def put_fragment(applicationId, fragmentId, formId, fieldName, fragmentFilename, fieldType, fieldOptions, API_ENDPOINT_URI, token):
    """Save data to CosmosDB (Fragments table) through API and send messages || APIを介してCosmosDBのFragments テーブルへデータを保存し、メッセージを送信する

    Args:
        applicationId (str): GUID for application image || フォーム入力画像につけられたGUID
        fragmentId (list): list of GUID for fragment images || フラグメント画像につけられたGUID のリスト
        formId（str): GUID which is generated on UWP-FormDef || GUID, UWP-FormDefで定義時につけられるID
        fieldName（list): field tags || フィールドのタグ名
        fragmentFilename (list): list of file names (fragment images) with extention || フラグメント画像の拡張子を含むファイル名のリスト
        fieldType (list): field type which is defined on UWP-FormDef || UWP-FormDefで定義される選択肢
        fieldOptions (list): actual data input by 2 operators || 2オペレータが入力した実際のデータ
    Returns:
        response（response): HTTP status code || HTTPステータスコード

    """
    print("fragmentId: {}".format(len(fragmentId)))
    url = API_ENDPOINT_URI + 'api/Application/' + applicationId + '/fragments'

    headers = {
        "accept": "application/json", 'Authorization': 'Bearer ' + token, "Content-Type": "application/json"
    }

    data = []
    data_detail = []

    for i in range(len(fragmentId)):
        data_detail = {
            "fragmentId": fragmentId[i],
            "applicationId": applicationId,
            "formId": formId,
            "fieldName": fieldName[i],
            "fragmentFilename": fragmentFilename[i],
            "fieldType": fieldType[i],
            "fieldOptions": fieldOptions[i],
            "value": ""
        }
        data.append(data_detail)
    response = requests.put(url, data=json.dumps(data), headers=headers)
    return response


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


def get_token(AZURE_AD_CLIENT_ID, AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_SECRET):
    """
    Args:
        AZURE_AD_CLIENT_ID: Azure client ID || AZUREのクライアントID
        AZURE_AD_TENANT_ID: Azure tenant ID || AZUREのテナントID
        AZURE_AD_CLIENT_SECRET: Azure client secret || AZUREのクライアント資格情報
    Returns:
        token（token): generated token || 取得したtoken
    """
    # Create application instance to generate token || tokenを取得するアプリインスタンスを作成
    app = msal.ConfidentialClientApplication(AZURE_AD_CLIENT_ID,   # client id
        authority="https://login.microsoftonline.com/" + AZURE_AD_TENANT_ID,  # tenant id
        client_credential=AZURE_AD_CLIENT_SECRET) # client secret

    # Reference || ユーザー名パスワードフローの制約は下記のページを参照
    # https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Username-Password-Authentication
    result = app.acquire_token_for_client([AZURE_AD_CLIENT_ID + "/.default"])
    token = result["access_token"]
    return token

input_img = sys.argv[1]
log_path = '../test/adls_log'

# Azure Data Lake Storage Gen2 connection || Azure Data Lake Storage Gen2 接続内容
FRAGMENT_STORAGE_ACCOUNT_NAME = os.environ['FRAGMENT_STORAGE_ACCOUNT_NAME']
FRAGMENT_STORAGE_ACCESS_KEY = os.environ['FRAGMENT_STORAGE_ACCESS_KEY']
FRAGMENT_STORAGE_CONTAINER_NAME = os.environ['FRAGMENT_STORAGE_CONTAINER_NAME']

# Azure Data Lake Storage Gen2 connection || Azure Data Lake Storage Gen2 接続内容
APPLICATION_STORAGE_ACCOUNT_NAME = os.environ['APPLICATION_STORAGE_ACCOUNT_NAME']
APPLICATION_STORAGE_ACCESS_KEY = os.environ['APPLICATION_STORAGE_ACCESS_KEY']
APPLICATION_STORAGE_CONTAINER_NAME = os.environ['APPLICATION_STORAGE_CONTAINER_NAME']

# Azure Data Lake Storage Gen2 connection || Azure Data Lake Storage Gen2 接続内容
PROCESSED_STORAGE_ACCOUNT_NAME = os.environ['PROCESSED_STORAGE_ACCOUNT_NAME']
PROCESSED_STORAGE_ACCESS_KEY = os.environ['PROCESSED_STORAGE_ACCESS_KEY']
PROCESSED_STORAGE_CONTAINER_NAME = os.environ['PROCESSED_STORAGE_CONTAINER_NAME'] # processed

# Azure AD Connection || Azure 接続内容
AZURE_AD_CLIENT_ID = os.environ['AZURE_AD_CLIENT_ID']
AZURE_AD_TENANT_ID = os.environ['AZURE_AD_TENANT_ID']
AZURE_AD_CLIENT_SECRET = os.environ['AZURE_AD_CLIENT_SECRET']

AZ_BATCH_JOB_ID = os.environ['AZ_BATCH_JOB_ID']
API_ENDPOINT_URI = os.environ['API_ENDPOINT_URI']

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

    applicationId, storagePath, applicationFileName = generate_application_info(input_img, APPLICATION_STORAGE_CONTAINER_NAME)

    token = get_token(AZURE_AD_CLIENT_ID, AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_SECRET)

    conf = get_json_API(storagePath, log_path, API_ENDPOINT_URI, token)
    coords, formId, fieldName, fieldType, fieldOptions, formExtent = get_coords(conf)

    field_imgs, fieldName = cut_into_fragments(coords, app_x_after, app_y_after, big_w_after, big_h_after, rectified_cv2_img, formExtent)

    fragmentId, fragmentFilename, blob_list = save_fragments(field_imgs, FRAGMENT_STORAGE_ACCOUNT_NAME, FRAGMENT_STORAGE_ACCESS_KEY, FRAGMENT_STORAGE_CONTAINER_NAME, log_path, fragment_size, _ex_flag)

    _fragment_info = generate_fragment_info(field_imgs, applicationId, fragmentId, fieldName, fragmentFilename)
    if _ex_flag is True:
        check_fragment_count(blob_list, fragmentId, log_path, _fragment_count_flag)

    # If _ex_flag is False (e.g. connection error, data size mismatching, mismatching number of images), input image is put back to Azure batch.
    # _ex_flagがFalse(接続でエラー、画像データサイズ不一致、画像枚数不一致）の場合、Batch処理へinput_imgを戻す
    if _fragment_count_flag is True:
        # API (application)
        result = put_application(applicationId, formId, applicationFileName, API_ENDPOINT_URI, token)
        if result.status_code == 200:
            print(result)
            # API (fragment)
            response = put_fragment(applicationId, fragmentId, formId, fieldName, fragmentFilename, fieldType, fieldOptions, API_ENDPOINT_URI, token)
            if response.status_code == 200:
                print(response)
            else:
                genarate_logger("Errors occoured. (put_fragment):" + str(response.status_code), log_path)
                sys.exit(1)
        else:
            genarate_logger("Errors occoured. (put_application):" + str(result.status_code), log_path)
            sys.exit(1)
        put_processed_img(input_img, download_filename, APPLICATION_STORAGE_ACCOUNT_NAME, APPLICATION_STORAGE_ACCESS_KEY, PROCESSED_STORAGE_ACCOUNT_NAME, PROCESSED_STORAGE_ACCESS_KEY, PROCESSED_STORAGE_CONTAINER_NAME, AZ_BATCH_JOB_ID)
        os.remove(download_filename)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

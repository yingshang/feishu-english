from core.tencent import speech_recognition
from feishu.helper import *
import os
from core.scenes import scene,school_scenes,academic_scenes
from core.responses import *
from datetime import datetime
import json
from core.config import *
from core.models import *
import string
from feishu.api import MessageApiClient

# init service
message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)

topics_list = ['随机话题','讲座','学校']
cwd = os.getcwd()
chatfile_path = os.path.join(cwd,'chatfile')


def text_choice(message_id,root_id,parent_id,message_type,msgcontent):
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filepath = os.path.join(chatfile_path, f"{now}.opus")

    characteristic = message_id

    if message_type == "text":
        text_content = json.loads(msgcontent)['text']
        insert_msg(message_id, root_id, parent_id, text_content, message_type, characteristic, 'receive', 'text')

        if text_content == "帮助列表":
            message_api_client.reply_send(message_id, feishu_help_text, 'post')

        elif text_content == "余额":
            hard_limit_usd, total_usage = check_price()
            resp_text = "授权金额:{}\n\n总共使用:{}".format(hard_limit_usd, total_usage)
            message_api_client.reply_send(message_id, resp_text, 'text')

        elif "查询" in text_content:
            text_content = text_content.replace("查询", "").strip()
            dia_choice(parent_id, root_id, message_id, text_content,characteristic)

        elif "英文播放" in text_content:
            text_content = text_content.replace("英文播放", "").strip()
            duration_ms = generate_audio(text_content, filepath, dialogue=0)
            filekey = message_api_client.upload_audio_file(filepath, duration_ms)
            message_api_client.reply_send(message_id, filekey, 'audio')

        elif "录入单词" in text_content:
            contents = text_content.replace("录入单词", "").strip().split("\n")
            new_words, total_words = read_write_words(contents)
            message_api_client.reply_send(message_id, f'录入单词完成,更新{new_words}个单词,总共{total_words}个单词', 'text')

        elif "词汇阅读" == text_content:
            words = get_random_words()
            if words != None:
                text_content = scene['词汇阅读'].format(",".join(words))
                dia_choice(parent_id, root_id, message_id, text_content,characteristic)
            else:
                resp_text = '触发错误，确定是否录入单词。'
                message_api_client.reply_send(message_id, resp_text, 'text')

        elif "英语对话" in text_content:
            content = text_content.replace("英语对话", "").strip()
            text_content = scene['英语对话'].format(content)
            update_dia_type(message_id,'audio')
            dia_choice(parent_id, root_id, message_id, text_content,characteristic,filepath)

        # 听力场景
        elif text_content in topics_list:
            update_dia_type(message_id,'audio')

            if text_content =='学校':
                sc_scene = random.choice(list(school_scenes.keys()))
                value = school_scenes[sc_scene]
                sc_selected = random.choice(value)
                content = scene[text_content].format(sc_scene,sc_selected,sc_scene)
                dia_choice(parent_id, root_id, message_id, content, characteristic, filepath,dialogue=1)
                return
            elif text_content=="讲座":
                content = scene[text_content].format(random.choice(academic_scenes))
            else:
                content = scene[text_content]
            dia_choice(parent_id, root_id, message_id, content,characteristic,filepath)

        elif "独立口语" == text_content:
            pass
            # title = random_speak_title()
            # duration_ms = generate_audio(title, filepath, dialogue=0)
            # filekey = message_api_client.upload_audio_file(filepath, duration_ms)
            # message_api_client.reply_send(message_id, filekey, 'audio')

        elif "口语评分" in text_content:
            content = text_content.replace("口语评分", "").strip()
            filepath = get_filepath_by_message_id(parent_id)

            wav_filepath = to_wavfile(filepath)
            msgs = pronunciation_assessment_continuous_from_file(content,wav_filepath)
            message_api_client.reply_send(message_id, msgs, 'text')


        elif "扮演" in text_content:
            content = text_content.replace("扮演", "").strip()
            text_content = scene['扮演角色'].format(content)
            update_dia_type(message_id,'audio')
            dia_choice(parent_id, root_id, message_id, text_content,characteristic, filepath)

        elif "词汇题" == text_content:
            words = get_random_words(1)
            if words != None:
                word = words[0]
                text_content = scene['词汇题'].format(word, word)
                dia_choice(parent_id, root_id, message_id, text_content,characteristic)

            else:
                resp_text = '触发错误，确定是否录入单词'
                message_api_client.reply_send(message_id, resp_text, 'text')

        else:
            update_dia_type(message_id,'audio')
            dia_choice(parent_id, root_id, message_id, text_content,characteristic,filepath)


    elif message_type == 'audio':
        audio_content = json.loads(msgcontent)
        file_key = audio_content['file_key']
        message_api_client.download_audio(message_id, file_key, filepath)
        #获取音频文本
        speech_text = speech_recognition(filepath, TencentSecretId, TencentSecretKey)
        insert_msg(message_id, root_id, parent_id, speech_text, message_type, characteristic,'receive','audio',file_key,filepath)

        dia_choice(parent_id, root_id, message_id, speech_text,characteristic,filepath)


def emoji_choice(root_id, parent_id,message_id,emoji_type,characteristic):
    random_string = ''.join(random.sample(string.ascii_lowercase + string.digits, 32))
    msg_id = "om_{}".format(random_string)
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filepath = os.path.join(chatfile_path, f"{now}.opus")

    #print(emoji_type)
    # 原文
    if emoji_type == 'THUMBSUP':
        resp_text = get_content_by_message_id(message_id)
        message_id,parent_id,root_id,content = message_api_client.reply_send(message_id, resp_text, 'text')
        insert_msg(message_id, root_id, parent_id, resp_text,'text', characteristic,'send','')

    # 单词分析
    elif emoji_type == 'HEART':
        resp_text = get_content_by_message_id(message_id)
        content = scene['单词分析'].format(resp_text)
        dia_choice(parent_id, root_id, message_id, content,characteristic,ingore_type=1)


    elif emoji_type == 'SMILE':
        content = scene['阅读题目']
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')
        dia_choice(parent_id, root_id, message_id, content,characteristic,ingore_type=1)


    elif emoji_type == 'Delighted':
        content = scene['阅读答案']
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')

        dia_choice(parent_id, root_id, message_id, content,characteristic,ingore_type=1)


    elif emoji_type == 'MUSCLE':
        resp_text = get_content_by_message_id(message_id)
        duration_ms = generate_audio(resp_text, filepath, dialogue=0)
        filekey = message_api_client.upload_audio_file(filepath, duration_ms)
        message_id,parent_id,root_id,content = message_api_client.reply_send(message_id, filekey, 'audio')
        insert_msg(message_id, root_id, parent_id, resp_text,'text', characteristic,'send','')


    elif emoji_type =='THANKS':
        resp_text = get_content_by_message_id(message_id)

        content = scene['语法批改'].format(resp_text)
        insert_msg(msg_id, root_id, message_id, content, 'text', characteristic, 'receive', '')

        dia_choice(parent_id, root_id, message_id, content, characteristic, ingore_type=1)
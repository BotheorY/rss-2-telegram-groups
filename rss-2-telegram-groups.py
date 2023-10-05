from menu import run_menu as rm, create_menu as cm
import core
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import functions
from telethon.errors.rpcerrorlist import SendAsPeerInvalidError
from constants import *
import os
import warnings
import utilities as ut
import asyncio
import validators

warnings.simplefilter("ignore")

try:
    client = TelegramClient(StringSession(core.get_string_session()), os.environ.get('BT_TELEGRAM_API_ID').strip(), os.environ.get('BT_TELEGRAM_API_HASH').strip())
except Exception as e:
    ...

async def do_run():

    async def get_private_group_id(invite_link):
        if isinstance(invite_link, str):
            invite_link = invite_link.strip()
            try:
                if validators.url(invite_link):
                    group = await client.get_entity(invite_link)
                    result = group.id
                    if isinstance(result, int):
                        return int(result)
                    if ut.is_integer(result):
                        return int(result)
                    else:
                        return result
            except Exception as e:
                ...
        return invite_link

    async def main_loop():
        print(">>> Start sending messages... <<<")
        for job_index, job in enumerate(core.jobs):
            print(f"\nStart processing job {job['name']}...")
            try:
                curr_time = ut.curr_time()
                if job['time_from'] and (curr_time < job['time_from']):
                    continue
                if job['time_to'] and (curr_time > job['time_to']):
                    continue
                rss = core.read_feed_rss(job['rss'])
                if not rss:
                    continue
                for rss_item in rss:
                    print(f"\n\tProcessing RSS item \"{rss_item['title']}\"...")
                    rss_item_sent = False
                    try:
                        if job['last_rss_items'] and (rss_item['id'] in job['last_rss_items']):
                            continue
                        content = rss_item['title'] + '; '
                        if rss_item['tags']:
                            content = content + ", ".join(rss_item['tags']) + '; '
                        if rss_item['summary']:
                            content = content + rss_item['summary']
                        if job['forbidden_words'] and any(substring.lower() in content.lower() for substring in job['forbidden_words']):
                            continue
                        if job['required_words'] and (not any(substring.lower() in content.lower() for substring in job['required_words'])):
                            continue
                        print("\tSending RSS item...")
                        if job['model_code']:
                            message = core.apply_model(job['model_code'], rss_item)
                        else:
                            message = rss_item['link']
                        if not message:
                            continue
                        for group_index, group in enumerate(job['groups']):
                            print(f"\t\tSending message to chat \"{group}\"...")
                            try:
                                group = await get_private_group_id(group)
                                #core.jobs[job_index]['groups'][group_index] = group
                                try:
                                    if not job['send_as']:
                                        raise SendAsPeerInvalidError("You can't send messages as an empty peer")
                                    await client(functions.messages.SendMessageRequest(
                                        peer = group,
                                        message = message,
                                        send_as = job['send_as'],
                                        silent = False,
                                        no_webpage = False
                                    ))
                                except SendAsPeerInvalidError as e:
                                    await client.send_message(entity = group, message = message, link_preview = True, silent = False)
                            except Exception as e:
                                print(f"\t\t[MESSAGE ERROR] {str(e)}")
                                print("\t\tMessage not sent.")
                            else:
                                print("\t\tMessage sent.")
                                rss_item_sent = True
                        if rss_item_sent:
                            new_last_rss_items = job['last_rss_items']
                            if not new_last_rss_items:
                                new_last_rss_items = []
                            new_last_rss_items.append(rss_item['id'])
                            core.jobs[job_index]['last_rss_items'] = new_last_rss_items
                    finally:
                        print("\tRSS item processed.\n\t__________\n")
                    break
            finally:
                print("Processing job completed.\n\n*************************\n")
        last_rss_items_count = len(core.jobs[job_index]['last_rss_items'])
        rss_count = len(rss)
        if last_rss_items_count > rss_count:
            del core.jobs[job_index]['last_rss_items'][:last_rss_items_count - rss_count]
        core.save_jobs()
        print(">>> Sending messages completed. <<<")

    try:
        await client.connect()
    except Exception as e:
        print(f"[CONNECTION ERROR] {str(e)}")
    else:
        if client.is_connected():
            await main_loop()
        else:
            print("Connection failed.")

def main() -> None:

    try:

        menu: dict =    {
                            "title": "MAIN MENU",
                            "items":    [
                                            {"title": "Add Job", "type": "func", "exec": "core.add_job"},
                                            {"title": "View Jobs...",
                                                "submenu":  {
                                                                "title": "View Job",
                                                                "subtitle": "Choose the Job to view:",
                                                                "items": "core.get_mnu_view_jobs"
                                                            }
                                            },
                                            {"title": "Delete Job...",
                                                "submenu":  {
                                                                "title": "Delete Job",
                                                                "subtitle": "Choose the Job to delete:",
                                                                "items": "core.get_mnu_delete_jobs"
                                                            }
                                            }
                                        ]
                        }
        err: list = [False, None, None]
        err_msg: str = None
        res = rm(cm(menu, err))

        if err[0]:
            err_msg = err[1]

        if res:
            if err_msg:
                err_msg = err_msg + " \n" + res
            else:
                err_msg = res

        if err_msg:
            raise Exception(err_msg)

    except Exception as e:
        if str(e):
            print(f"[ERROR] {str(e)}")


if __name__ == '__main__':
    if (core.config_mode):
        main()
    else:
        if core.set_rep and core.telegram_session:
            print('Running...')   
            try:
                asyncio.get_event_loop().run_until_complete(do_run())
            except Exception as e:
                ...
            finally:
                print("Quitting...")

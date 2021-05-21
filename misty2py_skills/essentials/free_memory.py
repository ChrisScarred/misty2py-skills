from misty2py_skills.utils.converse import success_parser_from_dicts
import os
from typing import Callable, Dict, List, Tuple

from misty2py_skills.utils.utils import get_abs_path


def get_non_system_assets(
    misty: Callable,
    assets: List = ["audio", "image", "video", "recording"],
) -> Dict:
    action = "_list"
    non_sys_assets = {}
    for asset in assets:
        data = misty.get_info(asset + action)
        result = data.get("result", [])
        for hit in result:
            name = hit.get("name")
            if not name:
                continue

            is_system = hit.get("systemAsset", True)
            if not is_system:
                if not non_sys_assets.get(asset):
                    non_sys_assets[asset] = []
                non_sys_assets[asset].append(name)
                print("Found a non-system asset of type `%s` named `%s`." % (asset, name))

    return non_sys_assets


def get_asset_properties(asset_type: str, file: str) -> Tuple[str, str, str]:
    if asset_type == "recording":
        params = {"Name": file, "Base64": "true"}
    else:
        params = {"FileName": file, "Base64": "true"}

    split_file_name = file.split(".")
    name = split_file_name[0]
    if len(split_file_name) > 1:
        ext = split_file_name[1]
    else:
        ext = "unknown"

    return params, name, ext


def save_base64_str(full_path: str, content: str, overwrite: bool = False) -> bool:
    if not overwrite and os.path.exists(full_path):
        print("File `%s` already exists, not overwriting." % full_path)
        return True

    try:
        with open(full_path, "w") as f:
            f.write(content)
        print("Asset saved into `%s`." % full_path)
        return True

    except:
        print("Failed to save the asset into `%s`" % full_path)
        return False


def save_assets(misty: Callable, assets: Dict, location: str) -> List[str]:
    failed_list = []
    action = "_file"
    for asset_type, files in assets.items():
        for file in files:
            params, name, ext = get_asset_properties(asset_type, file)
            response = misty.get_info(asset_type + action, params=params)
            result = response.get("result")

            if not result:
                failed_list.append(file)

            else:
                file_name = "%s_%s_%s_in_base64.txt" % (asset_type, name, ext)
                full_path = os.path.join(location, file_name)
                file_content = result.get("base64")
                if not file_content:
                    failed_list.append(file)
                else:
                    success = save_base64_str(full_path, file_content)
                    if not success:
                        failed_list.append(file)

    return failed_list


def delete_assets(misty: Callable, assets: Dict, ignore_list: List = []) -> List[str]:
    action = "_delete"
    delete_list = []

    for asset_type, files in assets.items():
        for file in files:
            if not file in ignore_list:
                if asset_type == "recording":
                    data = {"Name": file}
                else:
                    data = {"FileName": file}
                response = misty.perform_action(asset_type + action, data=data)
                status = response.get("status")
                if status:
                    if status == "Success":
                        print("Successfully deleted the asset `%s`." % file)
                        delete_list.append(file)
                    else:
                        print("Failed to delete the asset `%s`. Message: `%s`" % (file, response))

    return delete_list


def free_memory(
    misty: Callable,
    assets: List = ["audio", "image", "video", "recording"],
    save: bool = True,
    save_dir: str = "data",
) -> Dict:
    save_dir = get_abs_path(save_dir)
    enable_audio = misty.perform_action("audio_enable")
    enable_av = misty.perform_action("streaming_av_enable")
    enable_camera = misty.perform_action("camera_enable")

    assets_to_delete = get_non_system_assets(misty, assets=assets)
    deletion = {}

    if len(assets_to_delete) == 0:
        deletion["status"] = "Success"
        deletion["message"] = "No non-system files present."

    else:
        failed_to_save_list = []

        if save:
            failed_to_save_list = save_assets(misty, assets_to_delete, save_dir)

        deleted = delete_assets(misty, assets_to_delete, failed_to_save_list)

        if len(deleted) > 0:
            deletion["status"] = "Success"
            deletion["message"] = "Successfully deleted following assets: %s" % str(deleted)
        
        else:
            deletion["status"] = "Failed"
            deletion["message"] = "Failed to delete any assets."
    
    disable_audio = misty.perform_action("audio_disable")
    disable_av = misty.perform_action("streaming_av_disable")
    disable_camera = misty.perform_action("camera_disable")
      
    return success_parser_from_dicts(
        enable_audio=enable_audio, 
        enable_av=enable_av, 
        enable_camera=enable_camera, 
        deletion=deletion, 
        disable_audio=disable_audio, 
        disable_av=disable_av, 
        disable_camera=disable_camera
    )


if __name__ == "__main__":
    from misty2py_skills.utils.utils import get_misty
    print(free_memory(get_misty(), "data"))

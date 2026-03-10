import garth
import os
import json
from datetime import datetime
from loguru import logger
from .client import Client

class ActivityClient(Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def list_activities(self, count="1", start_date=None, end_date=None):
        """
        List activities from Garmin Connect
        """
        limit = 100 if count == "all" else int(count)
        start = 0
        all_activities = []
        
        while True:
            logger.debug(f"正在抓取活動列表 (start={start}, limit={limit})...")
            params = {"limit": limit, "start": start}
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date
                
            activities = garth.client.connectapi(
                "/activitylist-service/activities/search/activities",
                params=params
            )
            
            if not activities:
                logger.debug("沒有更多活動。")
                break
            
            all_activities.extend(activities)
            logger.debug(f"本次抓取到 {len(activities)} 個活動，目前累計: {len(all_activities)}")
            
            if count != "all" and len(all_activities) >= int(count):
                all_activities = all_activities[:int(count)]
                break
            
            if len(activities) < limit:
                break
            
            start += limit
            
        return all_activities

    def download_activity(self, activity, format="gpx", directory="./", original_time=False, desc=None, overwrite=True):
        """
        Download a single activity in specified format
        """
        activity_id = activity["activityId"]
        start_time_local = activity["startTimeLocal"] # Format: 2023-07-31 08:30:00
        start_time_gmt = activity["startTimeGMT"]
        
        # Calculate timezone offset
        try:
            # Handle both '2023-07-31 08:30:00' and '2023-07-31T08:30:00'
            local_dt = datetime.fromisoformat(start_time_local.replace(" ", "T"))
            # Garmin GMT time might be '2023-07-31 00:30:00.0Z' or similar
            gmt_clean = start_time_gmt.replace("Z", "+00:00").replace(" ", "T")
            gmt_dt = datetime.fromisoformat(gmt_clean).replace(tzinfo=None)
            
            offset_seconds = int((local_dt - gmt_dt).total_seconds())
            hours, remainder = divmod(abs(offset_seconds), 3600)
            minutes, _ = divmod(remainder, 60)
            sign = "+" if offset_seconds >= 0 else "-"
            tz_str = f"{sign}{hours:02d}{minutes:02d}"
            
            # activity_YYYY-mm-dd_HH-ii-ss+時區
            time_str = local_dt.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"activity_{time_str}{tz_str}"
        except Exception as e:
            logger.warning(f"解析時間失敗，使用活動 ID 作為檔名: {e}")
            filename = f"activity_{activity_id}"
        
        if not os.path.exists(directory):
            logger.debug(f"建立目錄: {directory}")
            os.makedirs(directory)
            
        if desc:
            description = activity.get("description", "")
            if description:
                # Limit description size if specified
                if isinstance(desc, str) and desc.isdigit():
                    description = description[:int(desc)]
                elif isinstance(desc, int):
                    description = description[:desc]
                # Replace space and illegal chars in filename
                description = "".join(c for c in description if c.isalnum() or c in ("-", "_")).strip()
                if description:
                    filename += f"_{description}"

        # 檢查檔案是否已存在 (提早檢查以節省 API 呼叫)
        # 注意: 這裡只能初步檢查檔名，如果是 original 格式 (zip -> fit)，
        # 完整的 filepath 可能包含 .fit 擴充限，我們在後續根據格式細分
        
        ext_map = {"gpx": "gpx", "tcx": "tcx", "json": "json", "original": "fit"}
        ext = ext_map.get(format, "unknown")
        target_filepath = os.path.join(directory, f"{filename}.{ext}")

        if not overwrite and os.path.exists(target_filepath):
            logger.info(f"檔案已存在，跳過下載: {target_filepath}")
            return target_filepath
        
        logger.debug(f"正在準備下載活動 {activity_id}，格式: {format}")
        
        import zipfile
        
        # Get extension and data
        if format == "json":
            data = garth.client.connectapi(f"/activity-service/activity/{activity_id}")
            ext = "json"
            filepath = os.path.join(directory, f"{filename}.{ext}")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            if format == "gpx":
                url = f"/download-service/export/gpx/activity/{activity_id}"
                ext = "gpx"
            elif format == "tcx":
                url = f"/download-service/export/tcx/activity/{activity_id}"
                ext = "tcx"
            elif format == "original":
                url = f"/download-service/files/activity/{activity_id}"
                ext = "zip"
            else:
                raise ValueError(f"不支援的格式: {format}")
                
            data = garth.client.download(url)
            filepath = os.path.join(directory, f"{filename}.{ext}")
            with open(filepath, "wb") as f:
                f.write(data)
            
            # If original format, it's a zip. Extract it to get .fit files.
            if format == "original":
                try:
                    logger.debug(f"正在解壓縮原始檔案: {filepath}")
                    with zipfile.ZipFile(filepath, "r") as zip_ref:
                        # Zip might contain multiple files, but usually it's one .fit
                        for zip_info in zip_ref.infolist():
                            # Keep original extension from zip (usually .fit)
                            zip_ext = os.path.splitext(zip_info.filename)[1]
                            target_name = f"{filename}{zip_ext}"
                            target_path = os.path.join(directory, target_name)
                            
                            # Extract and rename
                            with zip_ref.open(zip_info) as source, open(target_path, "wb") as target:
                                target.write(source.read())
                            
                            # Update filepath for subsequent operations (like utime)
                            old_zip_path = filepath
                            filepath = target_path
                            logger.trace(f"已解壓至: {filepath}")
                    
                    # Remove the original zip file
                    os.remove(old_zip_path)
                    logger.debug(f"已刪除原始 ZIP 檔案: {old_zip_path}")
                except Exception as e:
                    logger.error(f"解壓縮失敗: {e}")
                
        if original_time:
            # Set file time to activity start time (GMT)
            try:
                # Use gmt_dt if it was successfully calculated earlier
                if 'gmt_dt' in locals():
                    timestamp = gmt_dt.timestamp()
                    os.utime(filepath, (timestamp, timestamp))
                    logger.trace(f"已同步檔案時間為活動開始時間 (GMT): {filepath}")
            except Exception as e:
                logger.warning(f"無法設定原始時間於 {filepath}: {e}")
                
        logger.debug(f"活動下載完成: {filepath}")
        return filepath

    def upload_activity(self, **kwargs):
        pass

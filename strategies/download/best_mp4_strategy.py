from domain.i_download_strategy import IDownloadStrategy

class BestMp4Strategy(IDownloadStrategy):
    def get_format_spec(self) -> str:
        return "best[ext=mp4]"
    
    def get_name(self) -> str:
        return "Best MP4"
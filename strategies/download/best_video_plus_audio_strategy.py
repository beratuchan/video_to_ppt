from domain.i_download_strategy import IDownloadStrategy

class BestVideoPlusAudioStrategy(IDownloadStrategy):
    def get_format_spec(self) -> str:
        return "bestvideo[ext=mp4]+bestaudio"
    
    def get_name(self) -> str:
        return "Best Video+Audio (merge)"
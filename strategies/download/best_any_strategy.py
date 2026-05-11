from domain.i_download_strategy import IDownloadStrategy

class BestAnyStrategy(IDownloadStrategy):
    def get_format_spec(self) -> str:
        return "best"
    
    def get_name(self) -> str:
        return "Best Any"
import pandas as pd
from os.path import exists


class CSVReader:
    def __init__(self, file_name: str, ):
        self.file_name: str = file_name

    def _get(self) -> pd.DataFrame | None:
        if exists(self.file_name):
            return pd.read_csv(self.file_name, index_col=False)

    def _get_query(self, query: str):
        return self._get().query(query).to_dict('records')


class CSVReaderMulty:
    def __init__(self, base_dir: str):
        if not exists(base_dir):
            raise FileNotFoundError(base_dir)
        if not base_dir.endswith('/'):
            base_dir += '/'
        self.base_dir = base_dir

    def _get(self, file_path: str) -> pd.DataFrame | None:
        if exists(f'{self.base_dir}{file_path}'):
            return pd.read_csv(f'{self.base_dir}{file_path}', index_col=False)

    def _get_query(self, file_path: str, query: str):
        return self._get(file_path).query(query).to_dict('records')

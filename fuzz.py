import os
import io
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from multiprocessing.pool import ThreadPool
import requests
from requests.packages import urllib3

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)


urllib3.disable_warnings()

# Workers configurations
ASYNC_WORKERS_COUNT = 100  # How many threads will make http requests.
WORKERS_DECREMENTED_COUNT_ON_ERROR = 10  # Retry the fuzzing with x less workers, to decrease the load on the server.
STARTED_JOB_LOG_INTERVAL = 100  # Every x started jobs, a log will be written

# IO Configurations
DEFAULT_PATHS_LIST_FILE = 'words_lists/Filenames_or_Directories_Common.wordlist'
VALID_ENDPOINTS_FILE = 'endpoints.txt'

# HTTP Configuration
RESOURCE_EXISTS_STATUS_CODES = list(range(200, 300)) + [401, 402, 403]


# Logging configurations
LOGS_DIRECTORY_FULL_NAME = 'logs'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = logging.INFO
BACKUP_LOGS_FILES_COUNT = 5
FUZZING_LOGGER_NAME = 'fuzzing'
LOG_FILE_MAX_BYTES = 0.5 * 1000 * 1000  # 500 KB


getdata=[]
class SaveData(object):
    getdata.clear()
    def getData(a,b):
        data_item = {
            "a":a,
            "b":b
           }
        getdata.append(data_item)
        jsonString = json.dumps(getdata)
        jsonFile = open("data.json", "w")
        jsonFile.write(jsonString)
        jsonFile.close()
  

                           
                

class FilesFactory(object):
    files = []
    urls = []

    def read_files_from_directory(self, user_path):
        self.files = [os.path.join(user_path, f) for f in os.listdir(user_path) if os.path.isfile(os.path.join(user_path, f))]

    def read_lines_from_files(self):
        for l in self.files:
            h = open(l, 'r')
            self.urls += h.read().splitlines()

    def __init__(self,user_path):
        if os.path.isdir(user_path):
            self.read_files_from_directory(user_path)
            self.read_lines_from_files()
        elif(os.path.isfile(user_path)):
            self.files.append(user_path)
            self.read_lines_from_files()

class LoggerFactory(object):
    loggers = {}
    logging_level = LOGGING_LEVEL
    logging.basicConfig(stream=sys.stdout, level=logging_level,
                        format=LOG_FORMAT)

    # Modifying the logger's level to ERROR to prevent console spam
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    @staticmethod
    def get_logger(logger_name):
        """
        Gets a logger by it's name. Created the logger if it don't exist yet.
        :param logger_name: The name of the logger (identifier).
        :return: The logger instance.
        :returns: Logger
        """
        if logger_name not in LoggerFactory.loggers:
            LoggerFactory.loggers[logger_name] = LoggerFactory._get_logger(logger_name)
        return LoggerFactory.loggers[logger_name]

    @staticmethod
    def _get_logger(logger_name, logs_directory_path=LOGS_DIRECTORY_FULL_NAME):
        # Creating the logs folder if its doesn't exist
        if not os.path.exists(logs_directory_path):
            os.mkdir(logs_directory_path)

        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter(LOG_FORMAT)





        # Adding a rotating file handler
        rotating_file_handler = RotatingFileHandler(
            os.path.join(logs_directory_path, '{0}.log'.format(logger_name)), maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=BACKUP_LOGS_FILES_COUNT)
        rotating_file_handler.setFormatter(formatter)
        rotating_file_handler.setLevel(LOGGING_LEVEL)
        logger.addHandler(rotating_file_handler)

        return logger


class PathTraversal(object):
    def __init__(self):

        # edit
        list_file=DEFAULT_PATHS_LIST_FILE
        async_workers_count=ASYNC_WORKERS_COUNT
        output_file=VALID_ENDPOINTS_FILE
        resource_exists_status_codes=RESOURCE_EXISTS_STATUS_CODES

        self._logger = LoggerFactory.get_logger(FUZZING_LOGGER_NAME)
        self._base_url =" "
        self._list_file_path = list_file
        self._async_workers_count = async_workers_count
        self._output_file_path = output_file
        self._resource_exists_status_codes = resource_exists_status_codes
        self._active_paths_status_codes = {}
        self._checked_endpoints = {}
        self._endpoints_total_count = 0
        self._session = requests.session()




    def start(self, async_workers_count=ASYNC_WORKERS_COUNT):
        self._load_paths_list()
        self._logger.info(
            'Getting the endpoints of the website {0} with list file "{1}" and {2} async workers.'.format(
                self._base_url,
                self._list_file_path,
                async_workers_count))
        if 0 >= async_workers_count:
            self._logger.error('Seems like the site does not support fuzzing, as it has a DDOS protection engine.')
            return

        pool = ThreadPool(async_workers_count)
        try:
            tasks = []
            self._logger.debug('Preparing the workers...')
            for i, path in enumerate(self._paths):
                self._logger.debug('Started a worker for the endpoint {0}'.format(path))
                if i > i and i % STARTED_JOB_LOG_INTERVAL == 0:
                    self._logger.info('Started {0} workers'.format(i))

                path = path.strip()
                full_path = '/'.join([self._base_url, path])
                tasks.append(pool.apply_async(self.request_head, (full_path, path)))
            for t in tasks:
                status_code, full_path, path = t.get()
                self._checked_endpoints[path] = path
                if self._is_valid_status_code(status_code):
                    print(full_path)    #printing full path
                    SaveData.getData(str(status_code),full_path)

            self._save_output_log()
        except requests.ConnectionError as e:
            pool.terminate()
            self._logger.error(e)
            self._logger.warning('An error occured while fuzzing.'
                                 ' Retrying with less async workers to reduce the server load.')
            retry_workers_count = async_workers_count - WORKERS_DECREMENTED_COUNT_ON_ERROR
            self.start(retry_workers_count)





    def _is_valid_status_code(self, status_code):
        return status_code in self._resource_exists_status_codes


    def _save_output_log(self):
        """
        Saves the results to an output file.
        """
        full_status_codes = {'/'.join([self._base_url, p]): code for p, code in self._active_paths_status_codes.items()}
        output_lines = ['{0} : {1}'.format(path, code) for path, code in full_status_codes.items()]
        if 1 >= len(output_lines):
            self._logger.warning(
                'There were no discovered endpoints. consider using a different file from "words_list" directory')
        self._logger.info('The following endpoints are active:{0}{1}'.format(os.linesep, os.linesep.join(output_lines)))
        with open(self._output_file_path, 'a+') as output_file:
            output_lines.sort()
            output_file.write(os.linesep.join(output_lines))
        self._logger.info('The endpoints were exported to "{0}"'.format(self._output_file_path))



    def _load_paths_list(self):
        """
        Loads the list of paths from the configured status.
        """
        if not os.path.exists(self._list_file_path):
            raise FileNotFoundError('The file "{0}" does not exist.'.format(self._list_file_path))
        with open(self._list_file_path) as paths_file:
            paths = [p.strip().lstrip('/').rstrip('/') for p in paths_file.readlines()]
            paths = [p for p in paths if p not in self._active_paths_status_codes]
            if not self._endpoints_total_count:
                self._endpoints_total_count = len(paths)
            self._paths = paths


    def request_head(self, url, path):
        if url != '':
            res = self._session.head(url, verify=False, allow_redirects=True)
            return res.status_code, url, path


#directry traversal

class DirectlyTraversal(object):
    def __init__(self):

        # edit
        list_file=DEFAULT_PATHS_LIST_FILE
        async_workers_count=ASYNC_WORKERS_COUNT
        output_file=VALID_ENDPOINTS_FILE
        resource_exists_status_codes=RESOURCE_EXISTS_STATUS_CODES

        self._logger = LoggerFactory.get_logger(FUZZING_LOGGER_NAME)
        self._base_url =" "
        self._list_file_path = list_file
        self._async_workers_count = async_workers_count
        self._output_file_path = output_file
        self._resource_exists_status_codes = resource_exists_status_codes
        self._active_paths_status_codes = {}
        self._checked_endpoints = {}
        self._endpoints_total_count = 0
        self._session = requests.session()




    def start(self, async_workers_count=ASYNC_WORKERS_COUNT):
        self._load_paths_list()
        self._logger.info(
            'Getting the endpoints of the website {0} with list file "{1}" and {2} async workers.'.format(
                self._base_url,
                self._list_file_path,
                async_workers_count))
        if 0 >= async_workers_count:
            self._logger.error('Seems like the site does not support fuzzing, as it has a DDOS protection engine.')
            return

        pool = ThreadPool(async_workers_count)
        try:
            tasks = []
            self._logger.debug('Preparing the workers...')
            for i, path in enumerate(self._paths):
                self._logger.debug('Started a worker for the endpoint {0}'.format(path))
                if i > i and i % STARTED_JOB_LOG_INTERVAL == 0:
                    self._logger.info('Started {0} workers'.format(i))

                path = path.strip()
                full_path = '/'.join([self._base_url, path])
                tasks.append(pool.apply_async(self.request_head, (full_path, path)))
            for t in tasks:
                status_code, full_path, path = t.get()
                self._checked_endpoints[path] = path
                if self._is_valid_status_code(status_code):
                    self._active_paths_status_codes[path] = status_code

                    #print(full_path)    #printing full path
                    SaveData.getData(str("->"),full_path)

            self._save_output_log()
        except requests.ConnectionError as e:
            pool.terminate()
            self._logger.error(e)
            self._logger.warning('An error occured while fuzzing.'
                                 ' Retrying with less async workers to reduce the server load.')
            retry_workers_count = async_workers_count - WORKERS_DECREMENTED_COUNT_ON_ERROR
            self.start(retry_workers_count)





    def _is_valid_status_code(self, status_code):
        return status_code in self._resource_exists_status_codes


    def _save_output_log(self):
        """
        Saves the results to an output file.
        """
        full_status_codes = {'/'.join([self._base_url, p]): code for p, code in self._active_paths_status_codes.items()}
        output_lines = ['{0} : {1}'.format(path, code) for path, code in full_status_codes.items()]
        if 1 >= len(output_lines):
            self._logger.warning(
                'There were no discovered endpoints. consider using a different file from "words_list" directory')
        self._logger.info('The following endpoints are active:{0}{1}'.format(os.linesep, os.linesep.join(output_lines)))
        with open(self._output_file_path, 'a+') as output_file:
            output_lines.sort()
            output_file.write(os.linesep.join(output_lines))
        self._logger.info('The endpoints were exported to "{0}"'.format(self._output_file_path))



    def _load_paths_list(self):
        """
        Loads the list of paths from the configured status.
        """
        if not os.path.exists(self._list_file_path):
            raise FileNotFoundError('The file "{0}" does not exist.'.format(self._list_file_path))
        with open(self._list_file_path) as paths_file:
            paths = [p.strip().lstrip('/').rstrip('/') for p in paths_file.readlines()]
            paths = [p for p in paths if p not in self._active_paths_status_codes]
            if not self._endpoints_total_count:
                self._endpoints_total_count = len(paths)
            self._paths = paths


    def request_head(self, url, path):
        if url != '':
            res = self._session.head(url, verify=False, allow_redirects=True)
            return res.status_code, url, path

# #directry traversal

###simple test

class SimpleTest(object):
    def __init__(self):

        # edit
        list_file=DEFAULT_PATHS_LIST_FILE
        async_workers_count=ASYNC_WORKERS_COUNT
        output_file=VALID_ENDPOINTS_FILE
        resource_exists_status_codes=RESOURCE_EXISTS_STATUS_CODES

        self._logger = LoggerFactory.get_logger(FUZZING_LOGGER_NAME)
        self._base_url =" "
        self._list_file_path = list_file
        self._async_workers_count = async_workers_count
        self._output_file_path = output_file
        self._resource_exists_status_codes = resource_exists_status_codes
        self._active_paths_status_codes = {}
        self._checked_endpoints = {}
        self._endpoints_total_count = 0
        self._session = requests.session()




    def start(self, async_workers_count=ASYNC_WORKERS_COUNT):
        self._load_paths_list()
        self._logger.info(
            'Getting the endpoints of the website {0} with list file "{1}" and {2} async workers.'.format(
                self._base_url,
                self._list_file_path,
                async_workers_count))
        if 0 >= async_workers_count:
            self._logger.error('Seems like the site does not support fuzzing, as it has a DDOS protection engine.')
            return

        pool = ThreadPool(async_workers_count)
        try:
            tasks = []
            self._logger.debug('Preparing the workers...')
            for i, path in enumerate(self._paths):
                self._logger.debug('Started a worker for the endpoint {0}'.format(path))
                if i > i and i % STARTED_JOB_LOG_INTERVAL == 0:
                    self._logger.info('Started {0} workers'.format(i))

                path = path.strip()
                full_path = '/'.join([self._base_url, path])
                tasks.append(pool.apply_async(self.request_head, (full_path, path)))
            for t in tasks:
                status_code, full_path, path = t.get()
                self._checked_endpoints[path] = path

                # print(status_code, full_path)
                # display(status_code,full_path)
                SaveData.getData(str(status_code),full_path)


               # if self._is_valid_status_code(status_code):
                    #self._active_paths_status_codes[path] = status_code
                    #print(full_path)    #printing full path
                



            self._save_output_log()
        except requests.ConnectionError as e:
            pool.terminate()
            self._logger.error(e)
            self._logger.warning('An error occured while fuzzing.'
                                 ' Retrying with less async workers to reduce the server load.')
            retry_workers_count = async_workers_count - WORKERS_DECREMENTED_COUNT_ON_ERROR
            self.start(retry_workers_count)





    def _is_valid_status_code(self, status_code):
        return status_code in self._resource_exists_status_codes


    def _save_output_log(self):
        """
        Saves the results to an output file.
        """
        full_status_codes = {'/'.join([self._base_url, p]): code for p, code in self._active_paths_status_codes.items()}
        output_lines = ['{0} : {1}'.format(path, code) for path, code in full_status_codes.items()]
        if 1 >= len(output_lines):
            self._logger.warning(
                'There were no discovered endpoints. consider using a different file from "words_list" directory')
        self._logger.info('The following endpoints are active:{0}{1}'.format(os.linesep, os.linesep.join(output_lines)))
        with open(self._output_file_path, 'a+') as output_file:
            output_lines.sort()
            output_file.write(os.linesep.join(output_lines))
        self._logger.info('The endpoints were exported to "{0}"'.format(self._output_file_path))



    def _load_paths_list(self):
        """
        Loads the list of paths from the configured status.
        """
        if not os.path.exists(self._list_file_path):
            raise FileNotFoundError('The file "{0}" does not exist.'.format(self._list_file_path))
        with open(self._list_file_path) as paths_file:
            paths = [p.strip().lstrip('/').rstrip('/') for p in paths_file.readlines()]
            paths = [p for p in paths if p not in self._active_paths_status_codes]
            if not self._endpoints_total_count:
                self._endpoints_total_count = len(paths)
            self._paths = paths


    def request_head(self, url, path):
        if url != '':
            res = self._session.head(url, verify=False, allow_redirects=True)
            return res.status_code, url, path


###simple test

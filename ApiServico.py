#ApiServico foi desenvolvido com auxilio do chatGPT

import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os

class FastAPIService(win32serviceutil.ServiceFramework):
    _svc_name_ = "XMLFastAPI"
    _svc_display_name_ = "XML FastAPI Service"
    _svc_description_ = "Serviço que roda a API de XMLs de Entrada e Saída."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        # Comando para rodar a API
        script_path = os.path.join(os.path.dirname(__file__), "Api.py")
        subprocess.call(["uvicorn", f"{script_path}:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FastAPIService)

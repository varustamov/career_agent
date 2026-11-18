"""Opt-in in-process periodic search. Does not submit applications."""
import threading, time
class SearchScheduler:
 def __init__(self, action, clock=time.time):
  self.action=action; self.clock=clock; self.lock=threading.Lock(); self.enabled=False; self.interval=60; self.next_run=None; self.last_error=None; self.last_result=None; self.running=False
 def configure(self, enabled, interval):
  if not isinstance(enabled,bool) or not isinstance(interval,int) or isinstance(interval,bool) or not 60<=interval<=10080: raise ValueError('Interval must be 60–10080 minutes')
  with self.lock:
   self.enabled=enabled;self.interval=interval;self.next_run=self.clock()+interval*60 if enabled else None
  return self.status()
 def status(self):
  with self.lock: return {'enabled':self.enabled,'interval_minutes':self.interval,'next_run':self.next_run,'last_error':self.last_error,'last_result':self.last_result,'running':self.running}
 def tick(self, now=None):
  now=self.clock() if now is None else now
  with self.lock:
   if not self.enabled or self.running or self.next_run is None or now<self.next_run: return
   self.running=True;self.next_run=now+self.interval*60
  try:
   result=self.action()
   with self.lock: self.last_result=result;self.last_error=None
  except Exception as e:
   with self.lock: self.last_error=str(e)
  finally:
   with self.lock: self.running=False
 def start(self):
  def loop():
   while True:
    time.sleep(15);self.tick()
  threading.Thread(target=loop,daemon=True,name='career-search-scheduler').start()

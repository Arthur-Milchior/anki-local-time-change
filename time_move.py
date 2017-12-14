# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior arthur@milchior.fr
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Feel free to contribute to this code on https://github.com/Arthur-Milchior/anki-local-time-change
# Anki's add-on number: 
################
#Configuration:#
################

ahead = True
seconds = 0
minutes = 5
hours = 0
days = 0
weeks = 0
######################
#End of configuration#
######################
from aqt.update import LatestVersionFinder
import time
from aqt import mw
import anki.sync
import io
import gzip
import random


from anki.db import DB
from anki.utils import ids2str, intTime, json, platDesc, checksum
from anki.consts import *
from anki.hooks import runHook
import anki

# syncing vars
HTTP_TIMEOUT = 90
HTTP_PROXY = None
HTTP_BUF_SIZE = 64*1024


totalDay = days+ weeks*7
totalHour = hours+ totalDay*24
totalMinute = minutes + totalHour *60
totalSecond = seconds+ totalMinute * 60
if not ahead:
    totalSecond *= -1
print "time in seconds is %s."%totalSecond


def run(self):
    print "time run"
    if not self.config['updates']:
        return
    d = self._data()
    d['proto'] = 1
    try:
        r = anki.sync.requests.post(aqt.appUpdate, data=d)
        r.raise_for_status()
        resp = r.json()
    except:
        # behind proxy, corrupt message, etc
        print("update check failed")
        return
    if resp['msg']:
        self.newMsg.emit(resp)
    if resp['ver']:
        self.newVerAvail.emit(resp['ver'])
    print "run time in seconds is %s."%second
    diff = resp['time'] - time.time() + totalSecond
    if abs(diff) > 300:
        self.clockIsOff.emit(diff)
            
LatestVersionFinder.run=run

mw.setupAutoUpdate()
print "end time"


def sync(self):
    "Returns 'noChanges', 'fullSync', 'success', etc"
    self.syncMsg = ""
    self.uname = ""
    # if the deck has any pending changes, flush them first and bump mod
    # time
    self.col.save()
    # step 1: login & metadata
    runHook("sync", "login")
    meta = self.server.meta()
    self.col.log("rmeta", meta)
    if not meta:
        return "badAuth"
    # server requested abort?
    self.syncMsg = meta['msg']
    if not meta['cont']:
        return "serverAbort"
    else:
        # don't abort, but if 'msg' is not blank, gui should show 'msg'
        # after sync finishes and wait for confirmation before hiding
        pass
    rscm = meta['scm']
    rts = meta['ts']
    self.rmod = meta['mod']
    self.maxUsn = meta['usn']
    # this is a temporary measure to address the problem of users
    # forgetting which email address they've used - it will be removed
    # when enough time has passed
    self.uname = meta.get("uname", "")
    meta = self.meta()
    self.col.log("lmeta", meta)
    self.lmod = meta['mod']
    self.minUsn = meta['usn']
    lscm = meta['scm']
    lts = meta['ts']
    print "time sync"
    if abs(rts - lts +totalSecond) > 300:
        self.col.log("clock off")
        return "clockOff"
    if self.lmod == self.rmod:
        self.col.log("no changes")
        return "noChanges"
    elif lscm != rscm:
        self.col.log("schema diff")
        return "fullSync"
    self.lnewer = self.lmod > self.rmod
    # step 1.5: check collection is valid
    if not self.col.basicCheck():
        self.col.log("basic check")
        return "basicCheckFailed"
    # step 2: deletions
    runHook("sync", "meta")
    lrem = self.removed()
    rrem = self.server.start(
        minUsn=self.minUsn, lnewer=self.lnewer, graves=lrem)
    self.remove(rrem)
    # ...and small objects
    lchg = self.changes()
    rchg = self.server.applyChanges(changes=lchg)
    self.mergeChanges(lchg, rchg)
    # step 3: stream large tables from server
    runHook("sync", "server")
    while 1:
        runHook("sync", "stream")
        chunk = self.server.chunk()
        self.col.log("server chunk", chunk)
        self.applyChunk(chunk=chunk)
        if chunk['done']:
            break
    # step 4: stream to server
    runHook("sync", "client")
    while 1:
        runHook("sync", "stream")
        chunk = self.chunk()
        self.col.log("client chunk", chunk)
        self.server.applyChunk(chunk=chunk)
        if chunk['done']:
            break
    # step 5: sanity check
    runHook("sync", "sanity")
    c = self.sanityCheck()
    ret = self.server.sanityCheck2(client=c)
    if ret['status'] != "ok":
        # roll back and force full sync
        self.col.rollback()
        self.col.modSchema(False)
        self.col.save()
        return "sanityCheckFailed"
    # finalize
    runHook("sync", "finalize")
    mod = self.server.finish()
    self.finish(mod)
    return "success"

anki.sync.Syncer.sync = sync

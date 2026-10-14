#!/usr/bin/env python3
"""Smart Speed Video v5 TEST: FFmpeg fast path, automatic iOS audio fallback.

A normal compatible video follows the proven FFmpeg-only route.
If FFmpeg returns nonzero, the same shortcut is reopened with a versioned
FALLBACK signal. Shortcuts gets the original movie back from a-Shell,
uses its native iOS 17 Encode Media to normalize audio to AIFF, and retries
the validated Universal v4 video-copy plus audio route.

This is experimental, not to replace validated v4 without on-device testing.
"""
from __future__ import annotations
import argparse, copy, plistlib, uuid
from pathlib import Path
from urllib.parse import quote

NAME='⚡ Speed Video Smart v5.1'
SOURCE='__smart_source.mp4'
AUDIO='__smart_audio.aiff'
OUTPUT='__smart_result.mp4'
SPEEDS=('1.1','1.2','1.3','1.4','1.5')
GET='AsheKube.app.a-Shell-mini.GetFileIntent'
PUT='AsheKube.app.a-Shell-mini.PutFileIntent'
EXEC='AsheKube.app.a-Shell-mini.ExecuteCommandIntent'
COND='is.workflow.actions.conditional'

def uid(): return str(uuid.uuid4()).upper()

def ref(u,name,media=False):
    v={'Type':'ActionOutput','OutputUUID':u,'OutputName':name}
    if media: v['Aggrandizements']=[{'Type':'WFCoercionVariableAggrandizement','CoercionItemClass':'WFAVAssetContentItem'}]
    return {'Value':v,'WFSerializationType':'WFTextTokenAttachment'}

def action(ident,params):
    return {'WFWorkflowActionIdentifier':ident,'WFWorkflowActionParameters':params}

def cb(event):
    return 'shortcuts://run-shortcut?name='+quote(NAME,safe='')+'&input=text&text='+quote(event,safe='')

def exec_action(cmd,template):
    assert "'" not in cmd
    a=copy.deepcopy(template)
    a['WFWorkflowActionParameters'].update(command="sh -c '"+cmd+"'",UUID=uid(),openWindow='open',ShowWhenRun=False)
    return a

def fast(speed):
    movie=' '.join((
        'ffmpeg -hide_banner -loglevel error -nostats -y',
        f'-i "{SOURCE}" -map 0:v:0 -map 0:a:0? -c:v copy',
        f'-bsf:v "setts=pts=PTS/{speed}:dts=DTS/{speed}:duration=DURATION/{speed}"',
        f'-af "atempo={speed}" -c:a aac -b:a 192k -movflags +faststart "{OUTPUT}"'
    ))
    # a-Shell mini's ios_system sh_main is NOT a POSIX shell:
    # it supports only AND- or OR-linked command lists and cannot parse if/fi.
    # Also, mixing && and || in one list is not POSIX-compatible there:
    # on failed && ios_system returns before reaching the later ||.
    # NESTED sh is required: inner AND-chain handles success and returns a
    # nonzero failure to the outer OR-chain for the fallback callback.
    # Fixed filenames and filter expressions contain no spaces; only the
    # callback URL needs quoted protection inside the nested string.
    movie=movie.replace('"', '')
    success=f'open "{cb("FINALIZAR")}"'
    inner=f'rm -f {OUTPUT} && {movie} && {success}'
    quoted=inner.replace('\\', '\\\\').replace('"', '\\"')
    return f'sh -c "{quoted}" || open "{cb("FALLBACK_"+speed)}"'

def safe(speed):
    return ' '.join((
        f'ls -lh "{SOURCE}" "{AUDIO}" &&',
        'ffmpeg -hide_banner -loglevel info -stats -y',
        f'-analyzeduration 0 -probesize 32 -an -i "{SOURCE}" -i "{AUDIO}"',
        '-map 0:v:0 -map 1:a:0 -c:v copy',
        f'-bsf:v "setts=pts=PTS/{speed}:dts=DTS/{speed}:duration=DURATION/{speed}"',
        f'-af "atempo={speed}" -c:a aac -b:a 192k',
        f'-movflags +faststart "{OUTPUT}" && open "{cb("FINALIZAR")}"'
    ))

def build(donor,ios):
    orig=donor['WFWorkflowActions']
    assert len(orig)==15
    encoder=next(a for a in ios['WFWorkflowActions']
                 if a['WFWorkflowActionIdentifier']=='is.workflow.actions.encodemedia')
    assert encoder['WFWorkflowActionParameters']['WFMedia']['Value']['Type']=='ExtensionInput'
    assert orig[1]['WFWorkflowActionIdentifier']==GET
    assert orig[8]['WFWorkflowActionIdentifier']==PUT
    assert orig[11]['WFWorkflowActionIdentifier']==EXEC
    result=copy.deepcopy(donor)
    acts=copy.deepcopy(orig[:7])
    acts[1]['WFWorkflowActionParameters']['fileName']=OUTPUT
    acts[3]['WFWorkflowActionParameters']['command']=f'rm -f "{SOURCE}" "{AUDIO}" "{OUTPUT}"'

    for rate in SPEEDS:
        start=copy.deepcopy(orig[0]); gid=uid()
        pp=start['WFWorkflowActionParameters']
        pp['GroupingIdentifier']=gid
        pp['WFConditionalActionString']='FALLBACK_'+rate
        pp.pop('UUID',None)
        retrieve=copy.deepcopy(orig[1]);get_id=uid()
        retrieve['WFWorkflowActionParameters'].update(fileName=SOURCE,UUID=get_id)
        convert=copy.deepcopy(encoder);p=convert['WFWorkflowActionParameters']
        enc_id=uid();p['UUID']=enc_id
        p['WFMedia']=ref(get_id,'Arquivo',media=True)
        p['WFInput']=copy.deepcopy(p['WFMedia'])
        p.update(CustomOutputName='Converted Audio',WFMediaAudioOnly=True,WFMediaAudioFormat='AIFF',WFMediaSpeed='Normal',Metadata=False)
        audio_id=uid()
        rename=action('is.workflow.actions.setitemname',{
            'WFName':AUDIO,'WFInput':ref(enc_id,'Converted Audio'),
            'WFDontIncludeFileExtension':False,'UUID':audio_id
        })
        upload=copy.deepcopy(orig[8]);ap=upload['WFWorkflowActionParameters']
        ap.update(UUID=uid(),file=ref(audio_id,'Item Renomeado'),overwrite=True)
        acts.extend((start,retrieve,convert,rename,upload,exec_action(safe(rate),orig[11]),copy.deepcopy(orig[4])))
        end=copy.deepcopy(orig[6])
        end['WFWorkflowActionParameters'].update(GroupingIdentifier=gid,UUID=uid())
        acts.append(end)

    rename_movie=copy.deepcopy(orig[7])
    rename_movie['WFWorkflowActionParameters'].update(WFName=SOURCE,WFDontIncludeFileExtension=False)
    upload_movie=copy.deepcopy(orig[8])
    upload_movie['WFWorkflowActionParameters']['overwrite']=True
    acts.extend((rename_movie,upload_movie))
    menu=copy.deepcopy(orig[9]);menu['WFWorkflowActionParameters']['WFMenuItems']=[x+'×' for x in SPEEDS]
    acts.append(menu)
    for rate in SPEEDS:
        br=copy.deepcopy(orig[10]);br['WFWorkflowActionParameters']['WFMenuItemTitle']=rate+'×'
        acts.extend((br,exec_action(fast(rate),orig[11])))
    acts.append(copy.deepcopy(orig[14]))
    result['WFWorkflowActions']=acts

    begins=sum(a['WFWorkflowActionIdentifier']==COND and a['WFWorkflowActionParameters'].get('WFControlFlowMode')==0 for a in acts)
    ends=sum(a['WFWorkflowActionIdentifier']==COND and a['WFWorkflowActionParameters'].get('WFControlFlowMode')==2 for a in acts)
    assert begins==ends==6,(begins,ends)
    assert len(acts)==61,len(acts)
    ids=[a.get('WFWorkflowActionParameters',{}).get('UUID') for a in acts]
    ids=[x for x in ids if x]
    assert len(ids)==len(set(ids))
    cmds=[a['WFWorkflowActionParameters']['command'] for a in acts if a['WFWorkflowActionIdentifier']==EXEC and 'ffmpeg' in a['WFWorkflowActionParameters'].get('command','')]
    assert len(cmds)==10,len(cmds)
    fast_cmds=[c for c in cmds if 'analyzeduration 0' not in c]
    assert len(fast_cmds)==5
    assert all('if ffmpeg' not in x and '; then ' not in x for x in fast_cmds)
    assert all('sh -c "rm -f ' in x and ' || open ' in x for x in fast_cmds)
    for rate in SPEEDS:
        assert sum('FALLBACK_'+rate in c for c in cmds)==1
        assert any(f'atempo={rate}' in c and f'analyzeduration 0' in c for c in cmds)
    assert result['WFWorkflowMinimumClientVersion']==donor['WFWorkflowMinimumClientVersion']
    print(f'PASS: {len(acts)} actions; 5 fast paths and 5 iOS native-audio fallback branches')
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--donor',required=True,type=Path)
    ap.add_argument('--ios-ref',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    shortcut=build(plistlib.loads(args.donor.read_bytes()),plistlib.loads(args.ios_ref.read_bytes()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(plistlib.dumps(shortcut,fmt=plistlib.FMT_BINARY,sort_keys=False))

if __name__=='__main__': main()

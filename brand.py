#!/usr/bin/env python3
"""Rebrand extracted Zorin OS tree: name, logo, Plymouth boot animation. Nothing else is touched.
usage: brand.py ROOTFS ISO_TEXT_DIR INITRD_MAIN_DIR"""
import os,re,sys,shutil,io,base64
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
HERE=os.path.dirname(os.path.abspath(__file__))
R,ISO,IMAIN=sys.argv[1:4]
NEW='Kiyan OS'
src=Image.open(HERE+'/assets/logo.jpg').convert('RGB')
# ---- boot theme assets
W,H=1920,1080; sw,sh=src.size; r=max(W/sw,H/sh)
im=src.resize((int(sw*r)+1,int(sh*r)+1),Image.LANCZOS); l=(im.width-W)//2; t=(im.height-H)//2
bg=im.crop((l,t,l+W,t+H))
TH=HERE+'/theme/kiyan'
# ---- emblem
cx,cy,rad=512,238,178
em=src.crop((cx-rad,cy-rad,cx+rad,cy+rad)).resize((1024,1024),Image.LANCZOS).convert('RGBA')
m=Image.new('L',(1024,1024),0); ImageDraw.Draw(m).ellipse((30,30,994,994),fill=255)
em.putalpha(m.filter(ImageFilter.GaussianBlur(40)))
buf=io.BytesIO(); em.resize((512,512),Image.LANCZOS).save(buf,'PNG')
svg=('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512"><image width="512" height="512" xlink:href="data:image/png;base64,%s"/></svg>'%base64.b64encode(buf.getvalue()).decode())
names=re.compile(r'^(start-here|distributor-logo)(-ubuntu|-debian)?\.(png|svg)$|^zorin-logo(-text|-text-dark)?\.(png|svg)$')
n=0
for base in ('usr/share/icons','usr/share/pixmaps','usr/share/plymouth','usr/share/zorin-os-upgrader'):
    for dp,dn,fn in os.walk(os.path.join(R,base)):
        if '/help/' in dp or 'plymouth/themes' in dp: continue
        for f in fn:
            p=os.path.join(dp,f)
            if not names.match(f) or os.path.islink(p): continue
            if f.endswith('.svg'): open(p,'w').write(svg); n+=1; continue
            try: size=Image.open(p).size
            except Exception: continue
            if 'text' in f:
                s=min(size); c=Image.new('RGBA',size,(0,0,0,0)); e=em.resize((s,s),Image.LANCZOS); c.paste(e,((size[0]-s)//2,(size[1]-s)//2),e); c.save(p)
            else: em.resize(size,Image.LANCZOS).save(p)
            n+=1
print('logos replaced:',n)
def sub(path,pairs):
    t=open(path).read()
    for a,b in pairs: t=t.replace(a,b)
    open(path,'w').write(t)
sub(R+'/usr/lib/os-release',[('PRETTY_NAME="Zorin OS','PRETTY_NAME="'+NEW),('NAME="Zorin OS"','NAME="%s"'%NEW)])
sub(R+'/etc/lsb-release',[('Zorin OS',NEW)])
for f in ('etc/issue','etc/issue.net'): sub(R+'/'+f,[('Zorin OS',NEW)])
sub(R+'/etc/casper.conf',[('FLAVOUR="Zorin OS"','FLAVOUR="%s"'%NEW)])
for d in (R+'/usr/share/plymouth/themes/kiyan', IMAIN+'/usr/share/plymouth/themes/kiyan'):
    shutil.rmtree(d,ignore_errors=True); shutil.copytree(TH,d)
shutil.copy(R+'/usr/lib/x86_64-linux-gnu/plymouth/script.so',IMAIN+'/usr/lib/x86_64-linux-gnu/plymouth/script.so')
for link in (R+'/etc/alternatives/default.plymouth', IMAIN+'/usr/share/plymouth/themes/default.plymouth'):
    if os.path.lexists(link): os.remove(link)
    os.symlink('/usr/share/plymouth/themes/kiyan/kiyan.plymouth',link)
# ---- boot menus
for f in ('isolinux/menuentries.cfg','boot/grub/grub.cfg','boot/grub/loopback.cfg','.disk/info'):
    sub(ISO+'/'+f,[('Zorin OS',NEW),('Zorin-OS','Kiyan-OS')])
# GRUB menu: plain dark background, no logo anywhere (also blank the distro class icon)
gp=ISO+'/boot/grub/themes/zorin/background.png'; GW,GH=Image.open(gp).size
Image.new('RGB',(GW,GH),(5,10,22)).save(gp)
# Kiyan card (emblem + KIYAN, rounded corners) to the LEFT of the menu: never overlaps it, never stretched
card=src.crop((345,50,680,490)).resize((130,171),Image.LANCZOS).convert('RGBA')
mk=Image.new('L',(130*4,171*4),0); ImageDraw.Draw(mk).rounded_rectangle((0,0,130*4-1,171*4-1),radius=14*4,fill=255)
card.putalpha(mk.resize((130,171),Image.LANCZOS)); card.save(ISO+'/boot/grub/themes/zorin/kiyan-logo.png')
open(ISO+'/boot/grub/themes/zorin/theme.txt','a').write('\n+ image {\n\ttop = 20%\n\tleft = 50%-390\n\twidth = 130\n\theight = 171\n\tfile = "kiyan-logo.png"\n}\n')
ip=ISO+'/boot/grub/themes/zorin/icons/zorin.png'
if os.path.exists(ip): Image.new('RGBA',Image.open(ip).size,(0,0,0,0)).save(ip)
# keep the boot animation on screen for at least ~6 s: only waits if boot reaches the login screen earlier than 9 s of uptime
dd=R+'/etc/systemd/system/plymouth-quit.service.d'; os.makedirs(dd,exist_ok=True)
open(dd+'/kiyan-min-splash.conf','w').write("""[Service]
ExecStartPre=/bin/sh -c 'u=$(cut -d. -f1 /proc/uptime); [ "$u" -lt 9 ] && sleep $((9-u)); exit 0'
""")

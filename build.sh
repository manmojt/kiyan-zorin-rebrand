#!/bin/bash
# Build Kiyan OS = stock Zorin OS 18 Core + new name/logo/boot animation only.
set -euo pipefail
cd "$(dirname "$0")"; HERE=$PWD; W=${WORK:-$HERE/work}; mkdir -p $W; cd $W
URL=${ZORIN_URL:-https://ftp.nluug.nl/pub/os/Linux/distr/zorin/18/Zorin-OS-18.1-Core-64-bit.iso}
[ -f zorin.iso ] || curl -fL --retry 5 -o zorin.iso "$URL"
sudo rm -rf rootfs iso initrd_x; mkdir iso
xorriso -osirrox on -indev zorin.iso -extract /casper/filesystem.squashfs fs.squashfs \
  -extract /casper/initrd.zstd iso/initrd.zstd -extract /isolinux iso/isolinux -extract /boot/grub iso/boot_grub \
  -extract /.disk iso/disk >/dev/null 2>&1
chmod -R u+w iso; mkdir -p iso/boot; mv iso/boot_grub iso/boot/grub; mv iso/disk iso/.disk
sudo unsquashfs -f -d rootfs fs.squashfs >/dev/null; rm fs.squashfs
mkdir initrd_x; sudo unmkinitramfs iso/initrd.zstd initrd_x
sudo python3 "$HERE/brand.py" rootfs iso initrd_x/main
# register theme as the default alternative for installed systems too
sudo mount --bind /proc rootfs/proc; sudo mount --bind /sys rootfs/sys; sudo mount --bind /dev rootfs/dev
sudo chroot rootfs update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/kiyan/kiyan.plymouth 900
sudo chroot rootfs update-alternatives --set default.plymouth /usr/share/plymouth/themes/kiyan/kiyan.plymouth
sudo umount -l rootfs/dev rootfs/sys rootfs/proc
# live initrd
( for e in early early2 early3; do (cd initrd_x/$e && sudo sh -c 'find . -print0 | sort -z | cpio -0 -o -H newc -R 0:0 --quiet'); done
  (cd initrd_x/main && sudo sh -c 'find . -print0 | cpio -0 -o -H newc -R 0:0 --quiet | zstd -19 -T0 -q') ) > iso/initrd.new
sudo mksquashfs rootfs fs.new -comp zstd -Xcompression-level 15 -b 131072 -noappend -no-progress
SIZE=$(sudo du -sb rootfs | cut -f1)
printf "%s" "$SIZE" > fs.size
OUT=${OUT:-Kiyan-OS-18.1-Core.iso}
xorriso -indev zorin.iso -outdev "$OUT" -boot_image any replay \
  -map fs.new /casper/filesystem.squashfs -map iso/initrd.new /casper/initrd.zstd -map fs.size /casper/filesystem.size \
  -rm /casper/filesystem.squashfs.gpg -- \
  -map iso/isolinux/menuentries.cfg /isolinux/menuentries.cfg -map iso/boot/grub/grub.cfg /boot/grub/grub.cfg \
  -map iso/boot/grub/loopback.cfg /boot/grub/loopback.cfg -map iso/boot/grub/themes/zorin/background.png /boot/grub/themes/zorin/background.png \
  -map iso/.disk/info /.disk/info -volid "KIYAN_OS" -commit
ls -l "$OUT"

#!/bin/bash
# 讲解视频 V3 合成:21 段幻灯片 + 1 段演示(第11段)→ 最终 mp4(17-19 为经济适用型新增段)
# 用法: bash build_video.sh [PAD_SECONDS]   # PAD 为段间停留,默认 1.0
set -e
ROOT="/Users/yaya/SHU/2601/软件体系结构/campus-qa"
SLIDES=/tmp/slidehd
AUDIO="$ROOT/video/audio"
OUT="$ROOT/video/.build"
PAD="${1:-1.0}"
mkdir -p "$OUT"
LIST="$OUT/concat.txt"; : > "$LIST"

DEMO_DUR=60.2   # demo_frontend_v2.webm 实测

for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21; do
  SEG="$OUT/seg_$i.mp4"
  if [ "$i" = "11" ]; then
    # 演示录屏段:视频为准,旁白不足则静音填充
    ffmpeg -y -loglevel error -i "$ROOT/video/demo_frontend_v2.webm" -i "$AUDIO/seg$i.m4a" \
      -map 0:v -map 1:a -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 25 \
      -c:a aac -b:a 128k -af "apad" -ar 44100 \
      -t "$DEMO_DUR" "$SEG"
  else
    DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO/seg$i.m4a")
    TAIL=0; [ "$i" = "21" ] && TAIL=15   # 结尾致谢页额外定格
    TOT=$(python3 -c "print(f'{float('$DUR')+$PAD+$TAIL:.2f}')")
    ffmpeg -y -loglevel error -loop 1 -i "$SLIDES/s-$i.png" -i "$AUDIO/seg$i.m4a" \
      -c:v libx264 -tune stillimage -preset medium -crf 20 -pix_fmt yuv420p -r 25 \
      -vf "scale=1280:720:flags=lanczos" \
      -c:a aac -b:a 128k -af "apad" -ar 44100 \
      -t "$TOT" "$SEG"
  fi
  echo "file '$SEG'" >> "$LIST"
  echo "seg $i done"
done

ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a copy "$ROOT/video/智问校园CampusMind答辩讲解视频.mp4"
echo "=== FINAL ==="
ffprobe -v error -show_entries format=duration -of csv=p=0 "$ROOT/video/智问校园CampusMind答辩讲解视频.mp4"

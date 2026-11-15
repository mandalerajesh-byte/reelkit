"""Generate a synthetic 1080x1920 test video: tone / silence / tone / silence / tone."""
import subprocess, sys

def make(path="sample.mp4"):
    filt = (
        "sine=f=440:d=2[a0];anullsrc=r=44100:cl=mono,atrim=0:2[s0];"
        "sine=f=523:d=2[a1];anullsrc=r=44100:cl=mono,atrim=0:3[s1];"
        "sine=f=659:d=2[a2];"
        "[a0][s0][a1][s1][a2]concat=n=5:v=0:a=1[a]"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=0x224466:s=1080x1920:d=11:r=30",
        "-filter_complex", filt, "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path,
    ], check=True)

if __name__ == "__main__":
    make(sys.argv[1] if len(sys.argv) > 1 else "sample.mp4")

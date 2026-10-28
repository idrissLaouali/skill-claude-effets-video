#!/usr/bin/env python3
"""Transcrit ta vidéo mot par mot (en français par défaut) et écrit <video>_mots.json.

    python transcrire.py ma_video.mp4            # français
    python transcrire.py ma_video.mp4 --langue en

Sert à deux choses : caler un effet sur un mot (« quand je dis Claude »)
et créer les sous-titres (effet sous-titres, option mots=<fichier>).
"""
import argparse, json, os, sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video'); ap.add_argument('--langue', default='fr'); ap.add_argument('--modele', default='small')
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("BESOIN_WHISPER : lance d'abord  pip install faster-whisper")
    modele = WhisperModel(a.modele, device='auto', compute_type='int8')
    segments, _ = modele.transcribe(a.video, language=a.langue, word_timestamps=True, vad_filter=True)
    mots = [{'mot': w.word.strip(), 'debut': round(w.start, 2), 'fin': round(w.end, 2)} for sg in segments for w in (sg.words or []) if w.word.strip()]
    sortie = os.path.splitext(a.video)[0] + '_mots.json'
    json.dump({'mots': mots}, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for m in mots: print(f"{m['debut']:6.2f}  {m['mot']}")
    print('Enregistré :', sortie)


if __name__ == '__main__':
    main()

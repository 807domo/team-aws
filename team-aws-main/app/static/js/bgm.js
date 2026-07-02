/**
 * bgm.js - Web Audio APIによるプロシージャルBGM
 *
 * チップチューン風のループBGMをコードで生成する。
 * 外部ファイル不要。音量調節とミュート切替に対応。
 */
(function () {
  'use strict';

  var audioCtx = null;
  var gainNode = null;
  var isPlaying = false;
  var schedulerTimer = null;

  var toggleBtn = document.getElementById('bgm-toggle');
  var volumeSlider = document.getElementById('bgm-volume');

  // 設定復元
  var savedVolume = localStorage.getItem('bgm-volume');
  var savedMuted = localStorage.getItem('bgm-muted');
  var volume = savedVolume !== null ? parseInt(savedVolume) : 30;
  var isMuted = savedMuted === 'true';
  volumeSlider.value = volume;

  // メロディ定義（周波数Hz、C4=262, D4=294, E4=330, F4=349, G4=392, A4=440, B4=494）
  var NOTE = {
    C4: 262, D4: 294, E4: 330, F4: 349, G4: 392, A4: 440, B4: 494,
    C5: 523, D5: 587, E5: 659, F5: 698, G5: 784, A5: 880,
    R: 0 // 休符
  };

  // 明るく穏やかなメロディ（愛媛の温泉町をイメージ）
  var melody = [
    NOTE.E4, NOTE.G4, NOTE.A4, NOTE.G4,
    NOTE.E4, NOTE.D4, NOTE.C4, NOTE.D4,
    NOTE.E4, NOTE.G4, NOTE.A4, NOTE.C5,
    NOTE.B4, NOTE.A4, NOTE.G4, NOTE.R,
    NOTE.A4, NOTE.G4, NOTE.E4, NOTE.D4,
    NOTE.C4, NOTE.D4, NOTE.E4, NOTE.G4,
    NOTE.A4, NOTE.G4, NOTE.E4, NOTE.D4,
    NOTE.C4, NOTE.R, NOTE.C4, NOTE.R,
  ];

  // ベースライン
  var bass = [
    NOTE.C4, NOTE.R, NOTE.G4, NOTE.R,
    NOTE.C4, NOTE.R, NOTE.E4, NOTE.R,
    NOTE.F4, NOTE.R, NOTE.C4, NOTE.R,
    NOTE.G4, NOTE.R, NOTE.G4, NOTE.R,
    NOTE.A4, NOTE.R, NOTE.E4, NOTE.R,
    NOTE.F4, NOTE.R, NOTE.C4, NOTE.R,
    NOTE.G4, NOTE.R, NOTE.E4, NOTE.R,
    NOTE.C4, NOTE.R, NOTE.C4, NOTE.R,
  ];

  var TEMPO = 140; // BPM
  var NOTE_DURATION = 60 / TEMPO; // 1ノートの秒数
  var currentNote = 0;
  var nextNoteTime = 0;

  function initAudio() {
    if (audioCtx) return;
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    gainNode = audioCtx.createGain();
    gainNode.connect(audioCtx.destination);
    gainNode.gain.value = volume / 100 * 0.3; // 控えめな音量
  }

  function playNote(freq, time, duration, type, gainMult) {
    if (freq === 0) return; // 休符
    var osc = audioCtx.createOscillator();
    var noteGain = audioCtx.createGain();

    osc.type = type || 'square';
    osc.frequency.value = freq;

    noteGain.gain.setValueAtTime(0.001, time);
    noteGain.gain.linearRampToValueAtTime((gainMult || 0.15), time + 0.02);
    noteGain.gain.exponentialRampToValueAtTime(0.001, time + duration * 0.9);

    osc.connect(noteGain);
    noteGain.connect(gainNode);

    osc.start(time);
    osc.stop(time + duration);
  }

  function scheduleNotes() {
    while (nextNoteTime < audioCtx.currentTime + 0.2) {
      var idx = currentNote % melody.length;

      // メロディ（矩形波）
      playNote(melody[idx], nextNoteTime, NOTE_DURATION * 0.8, 'square', 0.12);

      // ベース（三角波、1オクターブ下）
      var bassFreq = bass[idx] ? bass[idx] / 2 : 0;
      playNote(bassFreq, nextNoteTime, NOTE_DURATION * 0.9, 'triangle', 0.08);

      nextNoteTime += NOTE_DURATION;
      currentNote++;
    }
  }

  function startBGM() {
    if (isPlaying) return;
    initAudio();
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    isPlaying = true;
    nextNoteTime = audioCtx.currentTime;
    schedulerTimer = setInterval(scheduleNotes, 100);
    updateIcon();
  }

  function stopBGM() {
    isPlaying = false;
    if (schedulerTimer) {
      clearInterval(schedulerTimer);
      schedulerTimer = null;
    }
    updateIcon();
  }

  function updateIcon() {
    if (!toggleBtn) return;
    if (isMuted || !isPlaying) {
      toggleBtn.textContent = '🔇';
    } else if (volume < 30) {
      toggleBtn.textContent = '🔈';
    } else if (volume < 70) {
      toggleBtn.textContent = '🔉';
    } else {
      toggleBtn.textContent = '🔊';
    }
  }

  // トグルボタン
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      if (isMuted || !isPlaying) {
        isMuted = false;
        startBGM();
      } else {
        isMuted = true;
        stopBGM();
      }
      localStorage.setItem('bgm-muted', isMuted);
    });
  }

  // 音量スライダー
  if (volumeSlider) {
    volumeSlider.addEventListener('input', function () {
      volume = parseInt(this.value);
      localStorage.setItem('bgm-volume', volume);
      if (gainNode) {
        gainNode.gain.value = volume / 100 * 0.3;
      }
      if (volume === 0) {
        isMuted = true;
        stopBGM();
      } else if (isMuted && volume > 0) {
        isMuted = false;
        startBGM();
      }
      localStorage.setItem('bgm-muted', isMuted);
      updateIcon();
    });
  }

  // 初回クリックで再生開始（autoplay制限対策）
  if (!isMuted) {
    document.addEventListener('click', function initPlay() {
      startBGM();
      document.removeEventListener('click', initPlay);
    }, { once: true });
  }

  updateIcon();
})();

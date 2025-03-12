# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main scripts to run audio classification."""

import argparse
import datetime
from threading import Thread
import time
import RPi.GPIO as GPIO

from audio_classifier import AudioClassifier
from audio_classifier import AudioClassifierOptions

QUIET_START = 23
QUIET_END = 10

PIN_RED_LED = 17
PIN_GREEN_LED = 27
PIN_TRIGGER = 19

p = None
punishment = 0


def trigger_us(t):
  global triggering_us
  triggering_us = True
  GPIO.output(PIN_GREEN_LED, True)
  GPIO.output(PIN_TRIGGER, True)

  time.sleep(t)

  GPIO.output(PIN_GREEN_LED, False)
  GPIO.output(PIN_TRIGGER, False)

  triggering_us = False


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def meow_present(result):
    for cat in result:
      # print(cat)
      if (cat.label == "Cat" or cat.label == "Meow") and cat.score > 0.1:
        return True
    return False

punishing = False
def punish(p_level):
  global punishing

  def _p():
    # Short beep
    if p_level < 3:
      trigger_us(0.25)

    # Multiple short beeps
    if p_level % 5 == 0:
      for _ in range(p_level):
        trigger_us(0.25)
        time.sleep(0.25)

    # Long beep every 3
    if p_level % 3 == 0:
      trigger_us(p_level/3*2)

    # Longer beeps after first 3
    else:
      trigger_us(p_level//3 * 0.5)

    punishing = False

  if not punishing:
    Thread(target=_p, daemon=True).start()
    

def run(model: str, max_results: int, score_threshold: float,
        overlapping_factor: float, num_threads: int,
        enable_edgetpu: bool) -> None:
  """Continuously run inference on audio data acquired from the device.

  Args:
    model: Name of the TFLite audio classification model.
    max_results: Maximum number of classification results to display.
    score_threshold: The score threshold of classification results.
    overlapping_factor: Target overlapping between adjacent inferences.
    num_threads: Number of CPU threads to run the model.
    enable_edgetpu: Whether to run the model on EdgeTPU.
  """
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(PIN_TRIGGER, GPIO.OUT)
  GPIO.setup(PIN_GREEN_LED, GPIO.OUT)
  GPIO.setup(PIN_RED_LED, GPIO.OUT)


  GPIO.output(PIN_TRIGGER, False)
  GPIO.output(PIN_RED_LED, False)
  GPIO.output(PIN_GREEN_LED, False)


  if (overlapping_factor <= 0) or (overlapping_factor >= 1.0):
    raise ValueError('Overlapping factor must be between 0 and 1.')

  if (score_threshold < 0) or (score_threshold > 1.0):
    raise ValueError('Score threshold must be between (inclusive) 0 and 1.')

  # Initialize the audio classification model.
  options = AudioClassifierOptions(
      num_threads=num_threads,
      max_results=max_results,
      score_threshold=score_threshold,
      enable_edgetpu=enable_edgetpu)
  classifier = AudioClassifier(model, options)

  # Initialize the audio recorder and a tensor to store the audio input.
  audio_record = classifier.create_audio_record()
  tensor_audio = classifier.create_input_tensor_audio()

  # We'll try to run inference every interval_between_inference seconds.
  # This is usually half of the model's input length to create an overlapping
  # between incoming audio segments to improve classification accuracy.
  input_length_in_second = float(len(
      tensor_audio.buffer)) / tensor_audio.format.sample_rate
  interval_between_inference = input_length_in_second * (1 - overlapping_factor)
  pause_time = interval_between_inference * 0.1
  last_inference_time = time.time()

  # Initialize a plotter instance to display the classification results.
  # Start audio recording in the background.
  audio_record.start_recording()

  print("Started!")
  meow_debounce = 0
  state = False
  ctr = 5
  punishment = 0

  # Loop until the user close the classification results plot.
  while True:
    if ctr % 10 == 0:
      GPIO.output(PIN_RED_LED, state)
      state = not state

    if ctr % 300 == 0:
      ctr = 0
      if punishment> 0:
        punishment -= 1

    ctr += 1

    # Wait until at least interval_between_inference seconds has passed since
    # the last inference.
    now = time.time()
    diff = now - last_inference_time
    if diff < interval_between_inference:
      time.sleep(pause_time)
      continue
    last_inference_time = now

    # Load the input audio and run classify.
    tensor_audio.load_from_audio_record(audio_record)
    result = classifier.classify(tensor_audio)

    if meow_present(result):
      GPIO.output(PIN_GREEN_LED, True)

      if meow_debounce == 0 or meow_debounce > 4:
        if time_in_range(datetime.time(QUIET_START, 0, 0), datetime.time(QUIET_END, 0, 0), datetime.datetime.now().time()):
          print(f"[{time.ctime()}] MEOWING DURING QUIET HOURS", punishment)

          punish(punishment)
          punishment += 1

        else:
          print(f"[{time.ctime()}] Meow not during quiet hours")
      meow_debounce += 1        
    else:
      GPIO.output(PIN_GREEN_LED, False)
      meow_debounce = 0


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model',
      help='Name of the audio classification model.',
      required=False,
      default='yamnet.tflite')
  parser.add_argument(
      '--maxResults',
      help='Maximum number of results to show.',
      required=False,
      default=5)
  parser.add_argument(
      '--overlappingFactor',
      help='Target overlapping between adjacent inferences. Value must be in (0, 1)',
      required=False,
      default=0.5)
  parser.add_argument(
      '--scoreThreshold',
      help='The score threshold of classification results.',
      required=False,
      default=0.0)
  parser.add_argument(
      '--numThreads',
      help='Number of CPU threads to run the model.',
      required=False,
      default=4)
  parser.add_argument(
      '--enableEdgeTPU',
      help='Whether to run the model on EdgeTPU.',
      action='store_true',
      required=False,
      default=False)
  args = parser.parse_args()

  try:
    run(args.model, int(args.maxResults), float(args.scoreThreshold),
        float(args.overlappingFactor), int(args.numThreads),
        bool(args.enableEdgeTPU))
  finally:
    GPIO.cleanup()

if __name__ == '__main__':
  main()

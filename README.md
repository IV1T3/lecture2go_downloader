# Lecture2Go Downloader

This is a Python tool for downloading videos from Lecture2Go at https://lecture2go.uni-hamburg.de.

## Description

This Python script fetches videos from the Lecture2Go platform either individually or as part of a series. It supports downloading videos that are protected by a password. Additionally, it provides the ability to select the desired video resolution, either minimum or maximum, depending on your requirements.

The script parses the website for metadata like title, date, and creator, and uses it to name the downloaded video files.

## Features

1. Download individual or all videos from a series.
2. Download password-protected videos.
3. Select between minimum and maximum resolution for the download.
4. Downloaded videos are named with date, creator, and title for easy organization.
5. Download progress indication with tqdm library.

## Installation

1. Clone this repository or download the Python file.

```bash
git clone https://github.com/IV1T3/lecture2go_downloader.git
```

2. Install the required Python dependencies.

```bash
pip install -r requirements.txt
```

## Usage

1. To run the script, use the following command:

```bash
python lecture2go_downloader.py --url <video_url> [--password <password>] [--all] [--resolution <min|max|manual>]
```

Where:

- `<video_url>`: URL of the Lecture2Go video or series you want to download.
- `<password>`: Password for the video, if it's protected.
- `--all`: Download all videos in a series (if applicable).
- `--resolution`: Choose to always download either minimum (`min`) or maximum (`max`) resolution. Default is `max`. You can also choose to select a resolution manually (`manual`) for each video, respectively.

For example, to download a single video, which is not password protected, at maximum resolution:

```bash
python lecture2go_downloader.py --url https://lecture2go.uni-hamburg.de/l2go/-/get/v/18368
```

Or to download all videos in a series at minimum resolution:

```bash
python lecture2go_downloader.py --url https://lecture2go.uni-hamburg.de/l2go/-/get/v/18368 --all --resolution min
```

Or to download all videos in a series with password protection in max resolution:

```bash
python lecture2go_downloader.py --url https://lecture2go\.uni-hamburg\.de/l2go/-/get/v/[a-zA-Z0-9]{24}$ --all --password mys3cr3tp4ssw0rd
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

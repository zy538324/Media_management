# Media Management System

A comprehensive media management solution to organize, request, and download your media library. This application integrates with popular services such as Jellyfin, Jackett, qBittorrent, TMDb, and Spotify.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Ubuntu/Linux Installation](#ubuntulinux-installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
  - [Setting Up Required APIs](#setting-up-required-apis)
  - [Additional Configuration](#additional-configuration)
- [Usage](#usage)
- [First-Time Setup](#first-time-setup)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

This Media Management System allows you to track, request, download, and organize your media collection. With integrations to popular media services, you can easily manage your entire library from a single interface.

## Features

- **Media Library Management**: Track your movies, TV shows, and music
- **Media Requests**: Allow users to request new content
- **Automated Downloads**: Automatically search and download requested media using Jackett and qBittorrent
- **Recommendations**: Get personalized recommendations based on your library from TMDb
- **Multi-user Support**: User account management with different permission levels
- **Jellyfin Integration**: Sync with your Jellyfin media server
- **Lightweight Database**: Uses SQLite for simple deployment and maintenance

## Requirements

- Python 3.8+
- qBittorrent (with Web UI enabled)
- Jackett
- Jellyfin (optional)
- API keys for:
  - TMDb
  - Spotify (optional)

## Installation

### Ubuntu/Linux Installation

We provide an automated installer for Ubuntu and other Linux distributions:

1. Download the installer script:

```bash
curl -O https://raw.githubusercontent.com/zy538324/Media_management/main/install_service.sh

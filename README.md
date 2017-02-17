# Kalliope LoxScontrol Neuron

[![Build Status](https://travis-ci.org/andweber/kalliope_neuron_loxone.svg?branch=master)](https://travis-ci.org/andweber/kalliope_neuron_loxone)
[![Gitter](https://badges.gitter.im/gitterHQ/gitter.svg)](https://gitter.im/kalliope-project/Lobby)

## Synopsis

This neuron allows to control a Loxone Homeautomation from [Kalliope](https://github.com/kalliope-project/kalliope/).

This project is a non-commercial community project and not connected to the company [Loxone](www.loxone.com).

## Installation

/!\ You need to have a running [Kalliope Core](https://github.com/kalliope-project/kalliope) installation. This is only a community module for Kalliope.

```
kalliope install --git-url https://github.com/kalliope-project/kalliope_neuron_loxone.git
```

For any further documentation about the usage of Kalliope, please refer to the [Kalliope project](https://github.com/kalliope-project/kalliope/).

## Options

| parameter | required | default | choices | comment    |
|-----------|----------|---------|---------|------------|
| lx_name  | YES      |         |         | User info. |
| lx_password  | YES      |         |         | User info. |

## Return Values

| Name     | Description                                  | Type | sample                                                       |
|----------|----------------------------------------------|------|--------------------------------------------------------------|
| status_code   | return value                    | str  |                                                             |
|   |   | |  |

## Synapses example

Simple example : 

```
  - name: "lx_turnon_light"
    signals:
      - order: "Turn on {{ lx_control_name }}"
    neurons:
      - loxScontrol:
          lx_user: "lx user name"
          lx_password: "my_password"
          say_template: 
            -  "Your order was {{ status_code }}."    
```

A complex example is included in brain_examples.

## Notes



## License

Copyright (c) 2017. All rights reserved.

Loxone is a registered trademark by the loxone company. See [www.loxone.com](www.loxone.com). 

Kalliope is covered by the MIT license, a permissive free software license that lets you do anything you want with the source code, 
as long as you provide back attribution and ["don't hold you liable"](http://choosealicense.com/). For the full license text see the [LICENSE.md](LICENSE.md) file.

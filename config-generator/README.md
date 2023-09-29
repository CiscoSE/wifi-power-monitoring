# Real devices

## Prerequisites

Install Dhall toolkit - for Linux:
```bash
cd <main-folder>

bash dependencies/install-deps-config-generator.sh
```

_Note_, for Mac and Windows, see corresponding packages here: https://github.com/dhall-lang/dhall-haskell/releases.

## Dhall-based configuration files generator

### Input

Create the following CSV files in [0.csv/csvs](./0.csv/csvs/) with the asset types:

| File   |      Asset type 
|----------|:-------------:|
| *sites.csv* | sites  |
| *zones.csv* | zones  |
| *switches.csv* | switches  |
| *aps.csv* | aps  |
 
See the [template files](./0.csv/templates/) as an example.

Sample `sites.csv`:
```
name,zone
site1,zone-A-1
site1,zone-A-2
site2,zone-B-1
```

Sample `zones.csv`:
```
name,site
zone-A-1,site1
zone-A-2,site1
zone-B-1,site2
```

Sample `switches.csv`:
```
name,zone,site,platform,ip,username,password,ssharguments
Switch1,zone-A-1,site1,cat9k,10.60.2.2,user1,tR1.;73,-oStrictHostKeyChecking=no -oKexAlgorithms=+diffie-hellman-group14-sha1
Switch2,zone-A-2,site1,cat9k,10.60.2.3,user2,tR1.;74,
Switch3,zone-B-1,site2,cat9k,10.60.2.4,user3,tR1.;74,
```

Sample `aps.csv`:
```
name,zone,switch,site
AP1,zone-A-1,Switch1,site1
AP2,zone-A-2,Switch1,site1
AP3,zone-B-1,Switch2,site2
```

### Output

[YAML files](./2.yaml) ([intermediary output in Dhall](./1.dhall))

### How to generate the YAML configuration files?

The conversion from CSV to YAML can be obtained with the following steps:

```bash
cd <main-folder>/config-generator

bash run-config-generator.sh
```

This will make the conversion from CSV -> DHALL and from DHALL -> YAML. The results will be stored in `../onboard/yaml` and `../onboard/testbed.yml`.
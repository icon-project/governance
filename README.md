Governance SCORE APIs
=====================

This document describes APIs that Governance SCORE provides.


# Overview

* Governance SCORE is a built-in SCORE that manages adjustable characteristics of ICON network.
* Address: cx0000000000000000000000000000000000000001

# Value Types

By default, Values in all JSON-RPC messages are in string form.
The most commonly used Value types are as follows.

| Value Type | Description | Example |
|:---------- |:------------|:--------|
| <a id="T_ADDR_EOA">T\_ADDR\_EOA</a> | "hx" + 40 digits HEX string | hxbe258ceb872e08851f1f59694dac2558708ece11 |
| <a id="T_ADDR_SCORE">T\_ADDR\_SCORE</a> | "cx" + 40 digits HEX string | cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32 |
| <a id="T_HASH">T\_HASH</a> | "0x" + 64 digits HEX string | 0xc71303ef8543d04b5dc1ba6579132b143087c68db1b2168786408fcbce568238 |
| <a id="T_INT">T\_INT</a> | "0x" + lowercase HEX string | 0xa |
| <a id="T_IMPORT_STMT">T\_IMPORT\_STMT</a> | Import statement string| "{'json': [], 'os': ['path'], 'base.exception': ['ExceptionCode']}" |
| <a id="T_BIN_DATA">T\_BIN\_DATA</a> | "0x" + lowercase HEX string (the length of string should be even) | 0x34b2 |
| <a id="T_SIG">T\_SIG</a> | base64 encoded string | VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA= |

## Import statement
### Grammar
import_stmt: "{" import_element ("," import_element)* "}" <br>
import_element: (import_name | import_from) <br>
import_name:  dotted_name ": []" <br>
Import_from:  dotted_name ": [" dotted_names "]" <br>
dotted_names: dotted_name ("," dotted_name) * <br>
dotted_name: "'"NAME ("." NAME)*"'" <br>
NAME: Not an empty string

### Examples
| python import | import statement |
|:------------- |:-----------------|
|import json | { 'json' : [] } |
|from json import * |{ 'json' : [] } |
|from os import path | { 'os' : ['path'] } |
|from base.exception import ExceptionCode | { 'base.exception' : ['ExceptionCode'] } |
|import json <br> from os import path <br> from base.exception import ExceptionCode <br> | { 'json' : [], 'os' : ['path'], 'base.exception' : ['ExceptionCode'] } |

# Methods List

* Query methods
    * [getScoreStatus](#getscorestatus)
    * [getStepPrice](#getstepprice)
    * [getStepCosts](#getstepcosts)
    * [getMaxStepLimit](#getmaxsteplimit)
    * [isDeployer](#isdeployer)
    * [isInScoreBlackList](#isinscoreblacklist)
    * [getVersion](#getVersion)
    * [isInImportWhiteList](#isinimportwhitelist)
    * [getServiceConfig](#getserviceconfig)
    * [getRevision](#getrevision)
* Invoke methods
    * [acceptScore](#acceptscore)
    * [rejectScore](#rejectscore)
    * [addAuditor](#addauditor)
    * [removeAuditor](#removeauditor)
    * [setStepPrice](#setstepprice)
    * [setStepCost](#setstepcost)
    * [setMaxStepLimit](#setmaxsteplimit)
    * [addDeployer](#adddeployer)
    * [removeDeployer](#removedeployer)
    * [addToScoreBlackList](#addtoscoreblacklist)
    * [removeFromScoreBlackList](#removefromscoreblacklist)
    * [addImportWhiteList](#addimportwhitelist)
    * [removeImportWhiteList](#removeimportwhitelist)
    * [updateServiceConfig](#updateserviceconfig)
    * [setRevision](#setrevision)
* Eventlog
    * [Accepted](#accepted)
    * [Rejected](#rejected)
    * [StepPriceChanged](#steppricechanged)
    * [StepCostChanged](#stepcostchanged)
    * [MaxStepLimitChanged](#maxsteplimitchanged)
    * [AddImportWhiteListLog](#addimportwhitelistlog)
    * [RemoveImportWhiteListLog](#removeimportwhitelistlog)
    * [UpdateServiceConfigLog](#updateserviceconfiglog)

# Query Methods

Query method does not change state. Read-only.

## getScoreStatus

* Queries the current status of the given SCORE.
* `current` indicates the currently active SCORE instance, while `next` is the SCORE code that has been requested to install or update, but not activated yet.
* [Fee 2.0] Checks the deposit information of the given SCORE.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_SCORE](#T_ADDR_SCORE) | a SCORE address to check the status |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getScoreStatus",
            "params": {
                "address": "cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32"
            }
        }
    }
}
```

#### Response: SCORE install case

```json
// Response - install requested: under auditing
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "next": {
            "status": "pending",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27"
        }
    }
}
```

```json
// Response - audit completed: accepted
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "current": {
            "status": "active",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27",
            "auditTxHash": "0x644dd57fbb65b49a49bcaf5e7685e01d53dc321f1cfb7dbbf8f4306265745292"
        }
    }
}
```

```json
// Response - audit completed: rejected
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "next": {
            "status": "rejected",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27",
            "auditTxHash": "0x644dd57fbb65b49a49bcaf5e7685e01d53dc321f1cfb7dbbf8f4306265745292"
        }
    }
}
```

#### Response: SCORE update case

```json
// Response - update requested: under auditing
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "current": {
            "status": "active",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b207",
            "auditTxHash": "0x644dd57fbb65b49a49bcaf5e7685e01d53dc321f1cfb7dbbf8f4306265745292"
        },
        "next": {
            "status": "pending",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b207"
        }
    }
}
```

```json
// Response - update requested, audit completed: rejected
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "current": {
            "status": "active",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27",
            "auditTxHash": "0x644dd57fbb65b49a49bcaf5e7685e01d53dc321f1cfb7dbbf8f4306265745292"
        },
        "next": {
            "status": "rejected",
            "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27",
            "auditTxHash": "0x644dd57fbb65b49a49bcaf5e7685e01d53dc321f1cfb7dbbf8f4306265745292"
        }
    }
}
```

#### Response: (Fee 2.0) SCORE deposit status

`depositInfo` field will be shown when there is a deposit in the SCORE.
```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "current": {
            "status": "active",
            "deployTxHash": "0x19793f41b8e64fc31190c6a70a103103da1f4bc81bc829fa72c852a5e388fe8c"
        },
        "depositInfo": {
            "scoreAddress": "cx216e1468b780ac1b54c328d19ea23a35a6899e55",
            "deposits": [
                {
                    "id": "0x64b118d4a3c2b3b93362a0f3ea06e5519de42449523465265b85509041e69011",
                    "sender": "hxe7af5fcfd8dfc67530a01a0e403882687528dfcb",
                    "depositAmount": "0x10f0cf064dd59200000",
                    "depositUsed": "0x0",
                    "created": "0x16",
                    "expires": "0x13c696",
                    "virtualStepIssued": "0x9502f9000",
                    "virtualStepUsed": "0x329a6"
                }
            ],
            "availableVirtualStep": "0x9502c665a",
            "availableDeposit": "0xf3f20b8dfa69d00000"
        }
    }
}
```

#### Response: error case

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "error": {
        "code": -32032,
        "message": "SCORE not found"
    }
}
```

## getStepPrice

* Returns the current step price in loop.

### Parameters

None

### Returns

`T_INT` - integer of the current step price in loop (1 ICX == 10^18 loop).

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getStepPrice"
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": "0x2540be400"
}
```

## getStepCosts

* Returns a table of the step costs for each actions.

### Parameters

None

### Returns

`T_DICT` - a dict:  key - camel-cased action strings, value - step costs in integer

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getStepCosts"
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "default": "0x186a0",
        "contractCall": "0x61a8",
        "contractCreate": "0x3b9aca00",
        "contractUpdate": "0x5f5e1000",
        "contractDestruct": "-0x11170",
        "contractSet": "0x7530",
        "get": "0x0",
        "set": "0x140",
        "replace": "0x50",
        "delete": "-0xf0",
        "input": "0xc8",
        "eventLog": "0x64",
        "apiCall": "0x2710"
    }
}
```

## getMaxStepLimit

* Returns the maximum step limit value that any SCORE execution should be bounded by.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| contextType | string | 'invoke' for sendTransaction, 'query' for call |

### Returns

`T_INT` - integer of the maximum step limit

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getMaxStepLimit",
            "params": {
                "contextType": "invoke"
            }
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": "0x9502f900"
}
```

## isDeployer

* Returns True if the given address can deploy SCORE.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_EOA](#T_ADDR_EOA) | EOA address to query |

### Returns

`T_INT` - "0x1" if the address is in the deployer list, otherwise "0x0"

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "isDeployer",
            "params": {
                "address": "hxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32"
            }
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": "0x1"
}
```

## isInScoreBlackList

* Returns "0x1" if the given address is in the deployer list.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_SCORE](#T_ADDR_SCORE) | SCORE address to query |

### Returns

`T_INT` - "0x1" if the SCORE address is in the black list, otherwise "0x0"

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "isInScoreBlackList",
            "params": {
                "address": "cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32"
            }
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": "0x1"
}
```



## getVersion

- Returns the version of Governance SCORE

### Returns

`T_STR` - version string

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getVersion"
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": "0.0.7"
}
```

## isInImportWhiteList

* Returns True if import statement is in the import white list.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| importStmt | [T\_IMPORT\_STMT](#T_IMPORT_STMT) | Import statement |

### Returns

`T_INT` - "0x1" if the import statement is in the import white list, otherwise "0x0"

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "isInImportWhiteList",
            "params": {
                "importStmt": "{'json': [], 'os': ['path'], 'base.exception': ['ExceptionCode']}"
            }
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": "0x0"
}
```

## getServiceConfig

* Returns table about server config.

### Parameters

None

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getServiceConfig"
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "FEE": "0x1",
        "AUDIT": "0x1",
        "DEPLOYER_WHITE_LIST": "0x0",
        "SCORE_PACKAGE_VALIDATOR": "0x1"
    }
}
```

## getRevision

* Returns info about revision.

### Parameters

None

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000001",
        "dataType": "call",
        "data": {
            "method": "getRevision"
        }
    }
}
```

#### Response

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "result": {
        "code": "0x4",
        "name": "1.3.0"
    }
}
```


# Invoke Methods

Invoke method can initiate state transition.

## acceptScore

* Accepts SCORE deployment request.
* This method can be invoked only from the addresses that are in the auditor list.
* The accepted SCORE will be executing from the next block.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| txHash | [T\_HASH](#T_HASH) | Transaction hash of the SCORE deploy transaction. |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "acceptScore",
            "params": {
                "txHash": "0xb903239f8543d04b5dc1ba6579132b143087c68db1b2168786408fcbce568238"
            }
        }
    }
}
```

## rejectScore

* Rejects SCORE deployment request.
* This can be invoked only from the addresses that are in the auditor list.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| txHash | [T\_HASH](#T_HASH) | Transaction hash of the SCORE deploy request. |
| reason | T\_TEXT | Reason for rejecting |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "rejectScore",
            "params": {
                "txHash": "0xb903239f8543d04b5dc1ba6579132b143087c68db1b2168786408fcbce568238",
                "reason": "SCORE cannot use network api"
            }
        }
    }
}
```

## addAuditor

* Adds a new address to the auditor list.
* Only the addresses registered in the auditor list can call `acceptScore` and `rejectScore`.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_EOA](#T_ADDR_EOA) | New EOA address that will be added to the auditor list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "addAuditor",
            "params": {
                "address": "hx2d54d5ca2a1dffbcfc3fb2c86cc07cb826f6b931"
            }
        }
    }
}
```

## removeAuditor

* Removes an address from the auditor list.
* The address removed from the auditor list cannot call `acceptScore` and `rejectScore` afterward.
* This function can be invoked only by either Governance SCORE owner or the auditor herself.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_EOA](#T_ADDR_EOA) | EOA address that is in the auditor list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "removeAuditor",
            "params": {
                "address": "hx2d54d5ca2a1dffbcfc3fb2c86cc07cb826f6b931"
            }
        }
    }
}
```

## setStepPrice

* Sets the current step price in loop.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| stepPrice | [T\_INT](#T_INT) | step price in loop (1 ICX == 10^18 loop) |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "setStepPrice",
            "params": {
                "stepPrice": "0x2540be400"
            }
        }
    }
}
```

## setStepCost

* Sets the step cost for a specific action of SCORE.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| stepType | [T\_STRING](#T_STRING) | action type |
| cost | [T\_INT](#T_INT) | step cost for the type |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "setStepCost",
            "params": {
                "stepType": "apiCall",
                "cost": "0x2710"
            }
        }
    }
}
```

## setMaxStepLimit

* Sets the maximum step limit value.
* Only the owner can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| contextType | [T\_STRING](#T_STRING) | 'invoke' for sendTransaction, 'query' for call |
| value | [T\_INT](#T_INT) | max value for the context |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "setMaxStepLimit",
            "params": {
                "contextType": "invoke",
                "value": "0x9502f900"
            }
        }
    }
}
```

## addDeployer

* Adds a new address to the deployer list.
* Deployer has the authority to register any SCORE without going through the audit process.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_EOA](#T_ADDR_EOA) | New EOA address that will be added to the deployer list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "addDeployer",
            "params": {
                "address": "hx2d54d5ca2a1dffbcfc3fb2c86cc07cb826f6b931"
            }
        }
    }
}
```

## removeDeployer

* Removes an address from the deployer list.
* The address removed from the deployer list cannot register SCORE afterward.
* This function can be invoked only by either Governance SCORE owner or the deployer herself.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_EOA](#T_ADDR_EOA) | EOA address that is in the deployer list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "removeDeployer",
            "params": {
                "address": "hx2d54d5ca2a1dffbcfc3fb2c86cc07cb826f6b931"
            }
        }
    }
}
```

## addToScoreBlackList

* Adds a new SCORE address to the black list, which is causing fatal problems in the network.
* SCOREs in the block list will not be invoked afterward. 
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_SCORE](#T_ADDR_SCORE) | New SCORE address that will be added to the black list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "addToScoreBlackList",
            "params": {
                "address": "cx2d54d5ca2a1dffbcfc3fb2c86cc07cb826f6b931"
            }
        }
    }
}
```

## removeFromScoreBlackList

* Removes the SCORE address from the black list.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| address | [T\_ADDR\_SCORE](#T_ADDR_SCORE) | SCORE address that is in the black list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "removeFromScoreBlackList",
            "params": {
                "address": "cx2d54d5ca2a1dffbcfc3fb2c86cc07cb826f6b931"
            }
        }
    }
}
```

## addImportWhiteList

* Adds a new import statement to the import white list
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| importStmt | [T\_IMPORT\_STMT](#T_IMPORT_STMT) | New import statement that will be added to the import white list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "addImportWhiteList",
            "params": {
                "importStmt": "{'json': [], 'os': ['path'], 'base.exception': ['ExceptionCode']}"
            }
        }
    }
}
```

## removeImportWhiteList

* Removes the import statement from the import white list.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| importStmt | [T\_IMPORT\_STMT](#T_IMPORT_STMT) | Import statement that is in the import white list |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "removeImportWhiteList",
            "params": {
                "importStmt": "{'json': [], 'os': ['path'], 'base.exception': ['ExceptionCode']}"
            }
        }
    }
}
```

## updateServiceConfig

* Updates the service config.
* This value is implemented using BitFlag
* Only the owner of the Governance SCORE can call this function.

### IconServiceConfig
| Key | BitFlag Value | Description |
|----|----|----|
| FEE | 1 | Enable Fee |
| AUDIT | 2 | Enable Audit |
| DEPLOYER\_WHITE\_LIST | 4 | Enable DeployerWhiteList |
| SCORE\_PACKAGE\_VALIDATOR | 8 | Enable SCORE Package Validator |

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| serviceFlag | [T\_INT](#T_INT) | flag for update service config|

### Examples
* Set value 3 if you want to activate service about Fee and Audit
* Set value 8 if you want to activate service about only SCORE Package Validator

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "updateServiceConfig",
            "params": {
                "serviceFlag": "0x1"
            }
        }
    }
}
```

## setRevision

* Sets the revision number and name.
* The revision number should be increased.
* Only the owner of the Governance SCORE can call this function.

### Parameters

| Key | Value Type | Description |
|:----|:-----------|-----|
| code | [T\_INT](#T_INT) | revision number |
| name | [T\_STRING](#T_STRING) | revision name |

### Examples

#### Request

```json
{
    "jsonrpc": "2.0",
    "id": 100,
    "method": "icx_sendTransaction",
    "params": {
        "version": "0x3",
        "from": "hxbe258ceb872e08851f1f59694dac2558708ece11",
        "to": "cx0000000000000000000000000000000000000001",
        "stepLimit": "0x30000",
        "timestamp": "0x563a6cf330136",
        "nonce": "0x1",
        "signature": "VAia7YZ2Ji6igKWzjR2YsGa2m53nKPrfK7uXYW78QLE+ATehAVZPC40szvAiA6NEU5gCYB4c4qaQzqDh2ugcHgA=",
        "dataType": "call",
        "data": {
            "method": "setRevision",
            "params": {
                "code": "0x4",
                "name": "1.2.3"
            }
        }
    }
}
```


# Eventlog

## Accepted

Triggered on any successful acceptScore transaction.

```python
@eventlog(indexed=1)
def Accepted(self, txHash: str):
    pass
```

## Rejected

Triggered on any successful rejectScore transaction.

```python
@eventlog(indexed=1)
def Rejected(self, txHash: str, reason: str):
    pass
```

## StepPriceChanged

Triggered on any successful setStepPrice transaction.

```python
@eventlog(indexed=1)
def StepPriceChanged(self, stepPrice: int):
    pass
```

## StepCostChanged

Triggered on any successful setStepCost transaction.

```python
@eventlog(indexed=1)
def StepCostChanged(self, stepType: str, cost: int):
    pass
```

## MaxStepLimitChanged

Triggered on any successful setMaxStepLimit transaction.

```python
@eventlog(indexed=1)
def MaxStepLimitChanged(self, contextType: str, value: int):
    pass
```

## AddImportWhiteListLog

Trigger on addImportWhiteList transaction change import white list.

```python
@eventlog(indexed=0)
def AddImportWhiteListLog(self, add_list: str, add_count: int):
    pass
```

## RemoveImportWhiteListLog

Trigger on removeImportWhiteList transaction change import white list.

```python
@eventlog(indexed=0)
def RemoveImportWhiteListLog(self, remove_list: str, remove_count: int):
    pass
```

## UpdateServiceConfigLog

Trigger on updateServiceConfig transaction.

```python
@eventlog(indexed=0)
def UpdateServiceConfigLog(self, serviceFlag: int):
    pass
```

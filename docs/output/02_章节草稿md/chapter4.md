## 第4章 多协议边缘网关软件系统设计与实现

### 4.1 软件系统总体设计

**模块化设计思想**

本系统软件设计遵循模块化、分层化的架构原则，将复杂的多协议网关功能分解为若干高内聚、低耦合的功能模块。每个模块承担明确的职责，通过定义良好的接口进行交互，便于独立开发、测试和维护。

软件架构自上而下划分为四个层次：应用服务层、业务逻辑层、协议适配层和硬件抽象层。应用服务层面向用户提供交互接口，包括Web管理后台和RESTful API；业务逻辑层实现设备管理、联动规则、数据缓存等核心功能；协议适配层处理异构协议的解析与转换；硬件抽象层封装底层硬件接口，向上层提供统一的操作接口。

**模块层次结构**

**表4-1 软件模块层次结构**

| 层次 | 模块名称 | 功能描述 | 技术实现 |
|-----|---------|---------|---------|
| 应用服务层 | Web管理台 | 提供可视化设备管理界面 | Flask + HTML/JavaScript |
| 应用服务层 | REST API | 提供外部系统对接接口 | Flask-RESTful |
| 业务逻辑层 | 设备管理器 | 设备注册、发现、状态维护 | Python Class |
| 业务逻辑层 | 联动引擎 | 本地自动化规则执行 | Node-RED |
| 业务逻辑层 | 数据缓存 | 离线数据存储与补传 | SQLite |
| 协议适配层 | Wi-Fi适配器 | TCP/UDP Socket数据收发 | Python Socket |
| 协议适配层 | BLE适配器 | 蓝牙GATT通信管理 | Bleak库 |
| 协议适配层 | MQTT适配器 | MQTT消息发布/订阅 | Paho-MQTT |
| 协议适配层 | 协议转换器 | 数据格式转换与封装 | JSON Schema |
| 硬件抽象层 | GPIO控制 | 树莓派GPIO接口操作 | RPi.GPIO |
| 硬件抽象层 | 串口通信 | UART设备通信 | PySerial |

模块间的依赖关系遵循单向原则：上层模块可调用下层模块的接口，但下层模块不依赖上层模块的具体实现。这种设计保证了核心功能（如协议适配）的稳定性，同时允许上层应用（如Web界面）独立演进。

### 4.2 统一数据传输模型与主题规范设计

**通用JSON数据格式定义**

为实现异构协议数据的标准化表示，本系统定义了一套通用的JSON数据格式。所有设备上报的数据和网关转发的消息均采用此格式封装，确保数据处理逻辑的一致性和可扩展性。

**表4-2 通用JSON数据格式字段定义**

| 字段名 | 数据类型 | 必填 | 说明 |
|-------|---------|-----|------|
| device_id | String | 是 | 设备唯一标识符，格式为"协议_类型_序号" |
| device_type | String | 是 | 设备类型，如temperature、light、humidity等 |
| protocol | String | 是 | 接入协议，枚举值：wifi、ble、zigbee |
| timestamp | Integer | 是 | 数据采集时间戳，Unix时间格式（秒） |
| location | String | 否 | 设备位置信息，如livingroom、bedroom |
| data | Object | 是 | 传感器数据对象，具体内容因设备类型而异 |
| status | String | 是 | 设备状态：online、offline、error |
| battery | Integer | 否 | 电池电量百分比（0-100），BLE设备特有 |

温度传感器数据示例：
```json
{
  "device_id": "wifi_temp_001",
  "device_type": "temperature",
  "protocol": "wifi",
  "timestamp": 1704067200,
  "location": "livingroom",
  "data": {
    "temperature": 25.6,
    "humidity": 58.2,
    "unit": "celsius"
  },
  "status": "online"
}
```

光照传感器数据示例：
```json
{
  "device_id": "ble_light_002",
  "device_type": "light",
  "protocol": "ble",
  "timestamp": 1704067200,
  "location": "bedroom",
  "data": {
    "illuminance": 350,
    "unit": "lux"
  },
  "status": "online",
  "battery": 85
}
```

**MQTT主题命名规范**

本系统遵循层次化的MQTT主题命名规范，采用"home/区域/设备类型/设备ID/数据类型"的五级结构。主题层级的划分既保证了设备标识的唯一性，又支持基于通配符的批量订阅和分组管理。

主题层级定义：
- 第一级（home）：根主题，标识智能家居系统
- 第二级（区域）：房间或功能区域，如livingroom、bedroom、kitchen、corridor等
- 第三级（设备类型）：设备功能分类，如temperature、humidity、light、motion等
- 第四级（设备ID）：设备唯一标识符，如sensor_001、lamp_002等
- 第五级（数据类型）：消息类型，data（数据上报）、control（控制指令）、status（状态查询）、config（配置信息）

主题示例：
- home/livingroom/temperature/sensor_001/data：客厅温度传感器数据
- home/bedroom/light/lamp_002/control：卧室灯具控制指令
- home/kitchen/motion/sensor_003/status：厨房人体传感器状态查询
- home/+/+/+/data：订阅所有设备的data主题（通配符+匹配单级）
- home/livingroom/#：订阅客厅所有设备的所有消息（通配符#匹配多级）

QoS等级选择策略：设备数据上报使用QoS 1（至少一次送达），确保数据可靠传输；控制指令使用QoS 1，保证指令到达；心跳消息使用QoS 0（最多一次），减少网络开销。

### 4.3 协议适配与数据收发模块设计实现

**Wi-Fi终端接入模块**

Wi-Fi终端接入模块负责管理ESP32-S3设备通过Wi-Fi网络与网关的通信连接。模块采用TCP Socket Server模式运行，监听指定端口（默认8888），等待设备连接建立。

程序逻辑架构：模块由主监听线程和多个设备处理线程组成。主监听线程持续监听端口，当检测到新的设备连接请求时，验证设备身份（通过预置的设备ID白名单），身份验证通过后创建独立的设备处理线程，专门负责与该设备的后续通信。

核心代码片段：
```python
class WiFiAdapter:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.devices = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        threading.Thread(target=self._accept_loop, daemon=True).start()
        
    def _accept_loop(self):
        while True:
            client_socket, address = self.server_socket.accept()
            device_thread = threading.Thread(
                target=self._handle_device,
                args=(client_socket, address),
                daemon=True
            )
            device_thread.start()
    
    def _handle_device(self, client_socket, address):
        device_id = self._authenticate(client_socket)
        if not device_id:
            client_socket.close()
            return
        self.devices[device_id] = client_socket
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                parsed_data = self._parse_wifi_frame(data)
                unified_msg = self._convert_to_unified_format(parsed_data)
                self._publish_to_mqtt(unified_msg)
            except Exception as e:
                logger.error(f"Device {device_id} error: {e}")
                break
        del self.devices[device_id]
        client_socket.close()
```

数据流处理流程：设备建立TCP连接后，首先发送身份注册帧，包含设备ID、设备类型等信息；网关验证通过后，进入数据通信阶段。设备周期性地发送传感器数据帧，帧格式采用简单的文本协议：设备ID、数据类型、数值、时间戳以逗号分隔，以换行符结束。网关接收到数据帧后，解析字段内容，填充至预定义的JSON模板，生成统一格式的消息。

**BLE终端接入模块**

BLE终端接入模块负责扫描、发现、连接BLE设备，并进行GATT特征值的读写操作。模块基于Bleak库（Bluetooth Low Energy platform Agnostic Klient）实现，该库提供了跨平台的Python异步BLE接口。

模块架构设计采用异步编程模型，充分利用Python asyncio库的高效并发处理能力。核心组件包括：扫描器（Scanner）定期扫描周围BLE广播设备；连接器（Connector）管理与目标设备的GATT连接；通知处理器（Notification Handler）处理设备主动推送的特征值变更通知；指令发送器（Command Sender）向设备下发控制指令。

核心代码片段：
```python
class BLEAdapter:
    def __init__(self):
        self.devices = {}
        self.connected_devices = {}
        self.scanner = BleakScanner()
        
    async def start_scan(self):
        self.scanner.register_detection_callback(self._on_device_detected)
        await self.scanner.start()
        
    def _on_device_detected(self, device, advertisement_data):
        device_id = self._extract_device_id(advertisement_data)
        if device_id and device_id.startswith('ble_'):
            self.devices[device_id] = device.address
            asyncio.create_task(self._connect_device(device.address, device_id))
    
    async def _connect_device(self, address, device_id):
        client = BleakClient(address)
        try:
            await client.connect()
            self.connected_devices[device_id] = client
            await client.start_notify(
                UART_TX_CHAR_UUID,
                lambda s, d: self._on_notification(device_id, s, d)
            )
        except Exception as e:
            logger.error(f"BLE connect error: {e}")
    
    def _on_notification(self, device_id, sender, data):
        parsed_data = self._parse_ble_payload(data)
        unified_msg = self._convert_to_unified_format(device_id, parsed_data)
        self._publish_to_mqtt(unified_msg)
```

GATT通信协议：BLE设备采用UART over BLE模式进行数据传输，使用Nordic UART Service（NUS）UUID定义服务。TX特征（UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E）用于设备向网关发送数据，RX特征（UUID: 6E400003-B5A3-F393-E0A9-E50E24DCCA9E）用于网关向设备发送指令。模块建立连接后订阅TX特征的通知，当设备上报数据时自动触发回调函数进行处理。

### 4.4 协议转换与消息路由模块设计实现

**异构协议数据标准化**

协议转换模块的核心功能是将Wi-Fi和BLE协议接收的原始数据，按照第4.2节定义的JSON规范进行标准化封装。转换过程包括字段映射、数据类型转换、时间戳统一和单位标准化四个步骤。

字段映射规则根据设备类型的不同有所差异。温度传感器的原始数据可能包含temp、humidity字段，映射后转换为data.temperature和data.humidity；光照传感器的原始数据可能为lux或light_value，统一映射为data.illuminance。协议转换器维护一个设备类型到字段映射规则的查找表，根据消息中的device_type字段选择对应的映射规则。

时间戳统一处理将各种格式的输入时间转换为Unix时间戳（秒级整数）。原始数据可能使用ISO 8601格式、本地时间字符串或相对时间偏移，转换器解析输入格式后统一输出标准时间戳。

单位标准化处理将不同协议的计量单位统一为国际标准。温度统一转换为摄氏度（celsius），光照统一转换为勒克斯（lux），湿度统一转换为百分比（percent）。

转换器核心代码逻辑：
```python
class ProtocolConverter:
    FIELD_MAPPING = {
        'temperature': {
            'temp': 'temperature',
            'humidity': 'humidity',
            'unit_temp': 'celsius'
        },
        'light': {
            'lux': 'illuminance',
            'light_value': 'illuminance',
            'unit': 'lux'
        }
    }
    
    def convert(self, raw_data, protocol):
        device_type = raw_data.get('type')
        mapping = self.FIELD_MAPPING.get(device_type, {})
        
        unified_data = {
            'device_id': raw_data.get('id'),
            'device_type': device_type,
            'protocol': protocol,
            'timestamp': self._normalize_timestamp(raw_data.get('time')),
            'location': raw_data.get('location', 'unknown'),
            'data': {},
            'status': 'online'
        }
        
        for raw_key, unified_key in mapping.items():
            if raw_key in raw_data:
                unified_data['data'][unified_key] = raw_data[raw_key]
        
        return json.dumps(unified_data)
```

**MQTT消息路由机制**

转换后的JSON消息通过MQTT客户端库（Paho-MQTT）发布到对应的主题。路由模块根据消息的device_type和location字段构造目标主题，实现消息的自动分类。

主题构造逻辑：
```python
def construct_topic(device_type, location, device_id, msg_type='data'):
    return f"home/{location}/{device_type}/{device_id}/{msg_type}"
```

消息发布流程：协议转换器输出的JSON消息首先放入消息队列；MQTT发布线程从队列中获取消息，解析内容构造主题，调用paho.mqtt.client.Client.publish()方法发布；发布回调函数记录消息的发送状态，QoS 1消息等待PUBACK确认后标记为发送成功，失败消息进入重试队列。

逻辑流程图：协议适配层接收原始数据 → 解析原始协议帧 → 提取有效载荷 → 根据设备类型选择映射规则 → 填充JSON模板 → 构造MQTT主题 → 发布至EMQX Broker → 消息路由至订阅者（Node-RED/Web后台/云端桥接）。

### 4.5 本地自治联动与离线补传机制实现

**Node-RED自动化联动流程**

Node-RED作为本地规则引擎，通过可视化节点编排实现设备联动的灵活配置。系统预置多种常用节点，用户通过拖拽连接即可构建自动化流程，无需编写代码。

联动规则配置示例——"光照自动控灯"场景：

1. mqtt-in节点：配置订阅主题为"home/+/light_sensor/+/data"，QoS 1，输出完整JSON消息。
2. function节点：编写处理逻辑，解析msg.payload中的data.illuminance字段，当数值低于100lux时返回开灯指令。
```javascript
// function节点代码
var illuminance = msg.payload.data.illuminance;
var threshold = flow.get('light_threshold') || 100;
if (illuminance < threshold) {
    msg.topic = msg.payload.location + '/light/lamp_001/control';
    msg.payload = { action: 'on', brightness: 80 };
    return msg;
}
return null;
```
3. mqtt-out节点：配置发布主题，接收function节点输出，向指定灯具发送控制指令。
4. debug节点：输出联动触发日志，便于调试和审计。

**温湿度异常报警场景**：mqtt-in节点订阅温度传感器数据；function节点判断是否超过阈值（如温度>35°C或湿度>80%），若超限构造报警消息；mqtt-out节点向报警主题发布消息；Web后台订阅报警主题，收到消息后推送浏览器通知。

**SQLite离线缓存与补传机制**

为实现断网自治和数据完整性保障，系统引入SQLite本地数据库，在网络中断时缓存无法上传的数据，待网络恢复后按时间戳顺序进行补传。

数据库表结构：
```sql
CREATE TABLE offline_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    qos INTEGER DEFAULT 1,
    retry_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

缓存机制实现：消息发布模块在发送前检查网络状态（通过检测与EMQX的连接状态或外部网络可达性）。当检测到网络中断时，将消息存入SQLite数据库而非直接发布；网络恢复后，后台补传线程按时间戳顺序读取缓存记录，重新发布至MQTT主题；发布成功后删除对应记录，失败则增加重试计数，超过最大重试次数（默认3次）后标记为失败并转存至异常日志表。

核心代码片段：
```python
class OfflineCacheManager:
    def __init__(self, db_path='offline_cache.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()
        
    def cache_message(self, topic, payload, qos=1):
        timestamp = int(time.time())
        with self.conn:
            self.conn.execute(
                'INSERT INTO offline_cache (timestamp, topic, payload, qos) VALUES (?, ?, ?, ?)',
                (timestamp, topic, json.dumps(payload), qos)
            )
    
    def get_pending_messages(self, limit=100):
        cursor = self.conn.execute(
            'SELECT id, timestamp, topic, payload, qos FROM offline_cache ORDER BY timestamp ASC LIMIT ?',
            (limit,)
        )
        return cursor.fetchall()
    
    def remove_message(self, msg_id):
        with self.conn:
            self.conn.execute('DELETE FROM offline_cache WHERE id = ?', (msg_id,))
    
    def increment_retry(self, msg_id):
        with self.conn:
            self.conn.execute(
                'UPDATE offline_cache SET retry_count = retry_count + 1 WHERE id = ?',
                (msg_id,)
            )
```

补传流程：网络状态监听器检测到网络恢复后，触发补传任务；补传线程查询缓存表获取待发送消息；逐条发布消息，成功则从缓存表删除，失败则增加重试计数；当重试次数超过阈值或缓存表为空时，结束本次补传任务。

### 4.6 设备管理与状态管理功能实现

**Flask Web管理后台架构**

Web管理后台基于Flask框架构建，提供RESTful API接口和HTML前端页面。采用应用工厂模式（Application Factory Pattern）组织代码，便于测试和配置管理。

项目结构：
```
gateway_web/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── models.py            # 数据库模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── device.py        # 设备管理路由
│   │   ├── auth.py          # 认证路由
│   │   └── system.py        # 系统配置路由
│   ├── services/
│   │   ├── device_service.py
│   │   └── mqtt_service.py
│   └── templates/           # Jinja2模板
│       └── *.html
├── config.py                # 配置文件
└── run.py                   # 启动入口
```

**设备注册与发现功能**

设备注册支持自动发现和手动添加两种模式。自动发现模式通过监听MQTT主题收集新设备上报的注册消息，自动创建设备记录；手动添加模式通过Web表单输入设备信息完成注册。

设备发现流程：网关启动时订阅"home/+/+/+/register"主题；新设备首次连接时向该主题发送注册消息，包含设备ID、类型、协议、位置等信息；Web后端接收到注册消息后，检查设备ID是否已存在，若不存在则创建设备记录，并向前端推送通知；用户在Web界面确认设备信息后，将其加入正式设备列表。

设备数据模型：
```python
class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.String(50), primary_key=True)
    device_type = db.Column(db.String(30), nullable=False)
    protocol = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(50))
    status = db.Column(db.String(10), default='offline')
    last_seen = db.Column(db.DateTime)
    battery_level = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.device_type,
            'protocol': self.protocol,
            'location': self.location,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'battery': self.battery_level
        }
```

**在线状态监测机制**

设备在线状态通过心跳超时机制进行判断。每个设备需定期（建议间隔30-300秒）发送心跳消息或数据上报消息，Web后端维护最后活跃时间戳，当超过设定阈值（默认5分钟）未收到消息时，将设备状态标记为离线。

状态监测实现：MQTT消息处理器在接收到设备消息时，更新设备的last_seen字段；定时任务每分钟扫描设备表，将last_seen早于当前时间减去超时阈值的设备标记为offline；状态变更时触发WebSocket通知，前端界面实时更新设备状态指示灯。

**日志查看与联动规则配置**

系统日志模块记录三类日志：设备通信日志（设备连接、断开、数据上报、指令下发记录）；联动触发日志（规则触发条件、执行动作、执行结果）；系统运行日志（服务启动、配置变更、错误异常）。日志存储于SQLite数据库，保留最近30天的记录，超过期限的日志自动归档或删除。

日志表结构：
```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    level TEXT CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
    source TEXT,
    message TEXT,
    details TEXT
);
```

联动规则配置界面通过调用Node-RED Admin API实现规则的新增、修改和删除。前端提供可视化表单，用户填写触发条件（设备、数据字段、比较运算符、阈值）和执行动作（目标设备、指令类型、参数），后端将表单数据转换为Node-RED流程JSON，通过HTTP POST请求部署至Node-RED运行时。

规则配置API示例：
```python
@device_bp.route('/api/rules', methods=['POST'])
def create_rule():
    data = request.get_json()
    rule_config = {
        'id': str(uuid.uuid4()),
        'label': data['name'],
        'nodes': [
            {
                'id': 'mqtt_in',
                'type': 'mqtt in',
                'topic': f"home/+/{data['trigger_device_type']}/+/data",
                'qos': 1
            },
            {
                'id': 'function',
                'type': 'function',
                'func': build_trigger_function(data['condition'])
            },
            {
                'id': 'mqtt_out',
                'type': 'mqtt out',
                'topic': f"home/+/{data['action_device']}/control"
            }
        ],
        'connections': [...]
    }
    nodered_api.deploy_flow(rule_config)
    return jsonify({'success': True, 'rule_id': rule_config['id']})
```

import React, { useState } from 'react';
import axios from 'axios';
import { Layout, Row, Col, Typography, Space, theme, Empty, Card } from 'antd';
import { BankOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import CreditForm from './components/CreditForm';
import ResultCard from './components/ResultCard';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { token } = theme.useToken();

  const handlePredict = async (values) => {
    setLoading(true);
    // Giả lập delay 
    setTimeout(async () => {
        try {
            const response = await axios.post('http://127.0.0.1:8000/predict', values);
            setResult(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    }, 800); 
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* HEADER: Logo & Branding */}
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        padding: '0 40px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        height: 72,
        zIndex: 10,
        background: '#C41E3A'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img 
            src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHuZOUGPjNdAesiuz6tJBIQrl7ilyOC3WbeA&s" 
            alt="HUST Logo" 
            style={{ height: 45 }} 
          />
          <div style={{ lineHeight: 1.2 }}>
            <Title level={4} style={{ margin: 0, color: '#fff', fontWeight: 800 }}>
              HUSTBANK
            </Title>
            <Text style={{ fontSize: 12, letterSpacing: 1, color: '#fff' }}>Hệ thống chấm điểm tín dụng thông minh</Text>
          </div>
        </div>
        <Space>
           <Text strong style={{ color: '#fff' }}><SafetyCertificateOutlined /> Cổng thông tin an toàn</Text>
        </Space>
      </Header>

      {/* BODY: Split Layout */}
      <Content style={{ padding: '30px 40px' }}>
        <Row gutter={32} style={{ height: 'calc(100vh - 140px)' }}> 
          
          {/* CỘT TRÁI: FORM NHẬP LIỆU */}
          <Col span={10} style={{ height: '100%' }}>
            <CreditForm onSubmit={handlePredict} isLoading={loading} />
          </Col>

          {/* CỘT PHẢI: KẾT QUẢ */}
          <Col span={14} style={{ height: '100%' }}>
            <div style={{ 
                height: '100%', 
                background: '#fff', 
                borderRadius: 12, 
                padding: 24,
                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
            }}>
                {result ? (
                    <ResultCard data={result} />
                ) : (
                    // Trạng thái chờ 
                    <Empty
                        image="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg"
                        imageStyle={{ height: 160 }}
                        description={
                            <div style={{ marginTop: 20 }}>
                                <Title level={4}>Chờ dữ liệu phân tích</Title>
                                <Text type="secondary">
                                    Vui lòng nhập thông tin hồ sơ vay bên trái và bấm "Phân tích" <br/>
                                    Hệ thống AI sẽ đánh giá rủi ro trong thời gian thực.
                                </Text>
                            </div>
                        }
                    />
                )}
            </div>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
}

export default App;
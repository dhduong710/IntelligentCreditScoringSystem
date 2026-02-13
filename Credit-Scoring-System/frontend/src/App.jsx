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
            const response = await axios.post('/predict', values);
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
        padding: '0 clamp(16px, 4vw, 40px)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        height: 'clamp(60px, 15vw, 72px)',
        zIndex: 10,
        background: '#C41E3A',
        flexWrap: 'wrap',
        gap: 8
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(8px, 2vw, 12px)' }}>
          <img 
            src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHuZOUGPjNdAesiuz6tJBIQrl7ilyOC3WbeA&s" 
            alt="HUST Logo" 
            style={{ height: 'clamp(32px, 8vw, 45px)' }} 
          />
          <div style={{ lineHeight: 1.2 }}>
            <Title level={4} style={{ margin: 0, color: '#fff', fontWeight: 800, fontSize: 'clamp(16px, 4vw, 20px)' }}>
              HUSTBANK
            </Title>
            <Text style={{ fontSize: 'clamp(10px, 2.5vw, 12px)', letterSpacing: 1, color: '#fff', display: window.innerWidth < 480 ? 'none' : 'inline' }}>Hệ thống chấm điểm tín dụng thông minh</Text>
          </div>
        </div>
        <Space style={{ display: window.innerWidth < 640 ? 'none' : 'flex' }}>
           <Text strong style={{ color: '#fff', fontSize: 'clamp(12px, 2.5vw, 14px)' }}><SafetyCertificateOutlined /> Cổng thông tin an toàn</Text>
        </Space>
      </Header>

      {/* BODY: Split Layout */}
      <Content style={{ padding: 'clamp(16px, 4vw, 30px) clamp(16px, 4vw, 40px)' }}>
        <Row gutter={[32, 24]} style={{ minHeight: 'calc(100vh - 140px)' }}> 
          
          {/* CỘT TRÁI: FORM NHẬP LIỆU */}
          <Col xs={24} lg={10} style={{ height: window.innerWidth >= 992 ? '100%' : 'auto' }}>
            <CreditForm onSubmit={handlePredict} isLoading={loading} />
          </Col>

          {/* CỘT PHẢI: KẾT QUẢ */}
          <Col xs={24} lg={14} style={{ height: window.innerWidth >= 992 ? '100%' : 'auto', minHeight: window.innerWidth < 992 ? '500px' : 'auto' }}>
            <div style={{ 
                height: '100%', 
                background: '#fff', 
                borderRadius: 12, 
                padding: 'clamp(16px, 4vw, 24px)',
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
                        imageStyle={{ height: 'clamp(100px, 25vw, 160px)' }}
                        description={
                            <div style={{ marginTop: 'clamp(12px, 3vw, 20px)' }}>
                                <Title level={4} style={{ fontSize: 'clamp(16px, 4vw, 20px)' }}>Chờ dữ liệu phân tích</Title>
                                <Text type="secondary" style={{ fontSize: 'clamp(13px, 3vw, 14px)' }}>
                                    Vui lòng nhập thông tin hồ sơ vay {window.innerWidth >= 992 ? 'bên trái' : 'ở trên'} và bấm "Phân tích" <br/>
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
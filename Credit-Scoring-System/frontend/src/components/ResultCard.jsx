import React from 'react';
import { Result, Tag, Typography, Statistic, Row, Col, Alert, List } from 'antd';
import { Gauge } from '@ant-design/plots';
import { CheckCircleFilled, CloseCircleFilled, InfoCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const ResultCard = ({ data }) => {
  if (!data) return null;

  const isApproved = data.status === "APPROVE";
  const scoreColor = isApproved ? '#52c41a' : '#f5222d'; 
  
  const config = {
    percent: data.probability,
    range: {
      color: 'l(0) 0:#52c41a 0.5:#faad14 1:#f5222d', 
    },
    indicator: {
      pointer: { style: { stroke: '#D0D0D0' } },
      pin: { style: { stroke: '#D0D0D0' } },
    },
    statistic: {
      content: {
        style: { fontSize: '36px', lineHeight: '36px', color: '#4B535E', fontWeight: 'bold' },
        formatter: () => `${(data.probability * 100).toFixed(1)}%`,
      },
    },
    gaugeStyle: {
        lineCap: 'round',
    },
  };

  return (
    <div style={{ padding: '0 20px', textAlign: 'center' }}>
      <Tag color={isApproved ? "success" : "error"} style={{ padding: '5px 15px', fontSize: 'clamp(12px, 3vw, 14px)', marginBottom: 20 }}>
         {isApproved ? "HỒ SƠ AN TOÀN" : "HỒ SƠ RỦI RO CAO"}
      </Tag>

      <Title level={2} style={{ color: scoreColor, margin: '10px 0', fontSize: 'clamp(18px, 5vw, 28px)' }}>
         {isApproved ? <CheckCircleFilled /> : <CloseCircleFilled />} {isApproved ? "HỒ SƠ ĐƯỢC DUYỆT" : "TỪ CHỐI KHOẢN VAY"}
      </Title>
      
      <Text style={{ fontSize: 'clamp(14px, 3vw, 16px)', display: 'block' }}>{data.message}</Text>

      <Row justify="center" align="middle" style={{ marginTop: 30, marginBottom: 20 }}>
         <Col span={24} style={{ height: 'clamp(180px, 40vw, 200px)' }}>
             <Gauge {...config} />
         </Col>
      </Row>

      {/* PHẦN HIỂN THỊ LÝ DO TỪ SHAP */}
      {data.reasons && data.reasons.length > 0 && (
        <div style={{ textAlign: 'left', marginTop: 20, marginBottom: 20 }}>
          <Alert
            message={
              <span style={{ fontWeight: 'bold', fontSize: 'clamp(13px, 3vw, 15px)' }}>
                 Yếu tố ảnh hưởng chính
              </span>
            }
            description={
              <List
                size="small"
                dataSource={data.reasons}
                renderItem={(item) => (
                  <List.Item style={{ padding: '4px 0', border: 'none' }}>
                    <Text style={{ fontSize: 'clamp(12px, 2.8vw, 14px)' }}>• {item}</Text>
                  </List.Item>
                )}
              />
            }
            type="error"
            showIcon={false}
            style={{ borderRadius: 8 }}
          />
        </div>
      )}

      <div style={{ background: '#f9f9f9', padding: 'clamp(12px, 4vw, 20px)', borderRadius: 8, marginTop: 20 }}>
        <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
                <Statistic 
                  title="Điểm Tín dụng" 
                  value={data.credit_score} 
                  valueStyle={{ color: scoreColor, fontWeight: 'bold', fontSize: 'clamp(20px, 5vw, 24px)' }}
                  style={{ fontSize: 'clamp(12px, 3vw, 14px)' }}
                />
            </Col>
            <Col xs={24} sm={12}>
                <Statistic 
                  title="Ngưỡng rủi ro hệ thống" 
                  value="15%"
                  valueStyle={{ fontSize: 'clamp(20px, 5vw, 24px)' }}
                  style={{ fontSize: 'clamp(12px, 3vw, 14px)' }}
                />
            </Col>
        </Row>
      </div>
    </div>
  );
};

export default ResultCard;
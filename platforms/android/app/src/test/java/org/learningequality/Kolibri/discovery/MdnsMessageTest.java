package org.learningequality.Kolibri.discovery;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.KITCHEN;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.LIBRARY;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.LIBRARY_RESPONSE;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.PRINTER;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.PTR_QUERY;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.PTR_RESPONSE;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.TABLET;
import static org.learningequality.Kolibri.discovery.ZeroconfFixtures.bytes;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class MdnsMessageTest {

  private static MdnsMessage parse(String hex) {
    byte[] data = bytes(hex);
    return MdnsMessage.parse(data, data.length);
  }

  private static MdnsMessage.Record onlyRecord(MdnsMessage message, int type) {
    List<MdnsMessage.Record> matching = new ArrayList<>();
    for (MdnsMessage.Record record : message.getRecords()) {
      if (record.getType() == type) {
        matching.add(record);
      }
    }
    assertEquals(1, matching.size());
    return matching.get(0);
  }

  @Test
  public void query_matchesTheQueryZeroconfSends() {
    assertArrayEquals(
        bytes(PTR_QUERY), MdnsMessage.query(ServerDiscovery.SERVICE_NAME, MdnsMessage.TYPE_PTR));
  }

  @Test
  public void parse_readsTheQuestionsOfAQuery() {
    byte[] query = MdnsMessage.query(LIBRARY, MdnsMessage.TYPE_SRV, MdnsMessage.TYPE_TXT);

    MdnsMessage message = MdnsMessage.parse(query, query.length);

    assertFalse(message.isResponse());
    assertEquals(2, message.getQuestions().size());
    assertEquals(LIBRARY, message.getQuestions().get(0).getName());
    assertEquals(MdnsMessage.TYPE_SRV, message.getQuestions().get(0).getType());
    assertEquals(LIBRARY, message.getQuestions().get(1).getName());
    assertEquals(MdnsMessage.TYPE_TXT, message.getQuestions().get(1).getType());
  }

  @Test
  public void parse_readsTheInstanceNamesOfAPtrAnswer() {
    MdnsMessage message = parse(PTR_RESPONSE);

    assertTrue(message.isResponse());
    List<String> targets = new ArrayList<>();
    for (MdnsMessage.Record record : message.getRecords()) {
      assertEquals(MdnsMessage.TYPE_PTR, record.getType());
      assertEquals(ServerDiscovery.SERVICE_NAME, record.getName());
      targets.add(record.getTarget());
    }
    assertEquals(Arrays.asList(LIBRARY, KITCHEN, TABLET, PRINTER), targets);
  }

  @Test
  public void parse_readsTheSrvPortAndTarget() {
    MdnsMessage.Record srv = onlyRecord(parse(LIBRARY_RESPONSE), MdnsMessage.TYPE_SRV);

    assertEquals(LIBRARY, srv.getName());
    assertEquals(8080, srv.getPort());
    assertEquals("library.kolibri.local.", srv.getTarget());
  }

  @Test
  public void parse_readsTheAdditionalAddressRecord() {
    MdnsMessage.Record address = onlyRecord(parse(LIBRARY_RESPONSE), MdnsMessage.TYPE_A);

    assertEquals("library.kolibri.local.", address.getName());
    assertEquals("192.168.1.20", address.getAddress());
  }

  @Test
  public void parse_readsTheTxtEntriesStillJsonEncoded() {
    MdnsMessage.Record txt = onlyRecord(parse(LIBRARY_RESPONSE), MdnsMessage.TYPE_TXT);

    assertEquals(LIBRARY, txt.getName());
    assertEquals("\"library\"", txt.getTxt().get("instance_id"));
    assertEquals("\"Library\"", txt.getTxt().get("device_name"));
    assertEquals("\"FALSE\"", txt.getTxt().get("subset_of_users_device"));
    assertEquals("\"/kolibri/\"", txt.getTxt().get("prefix"));
  }

  @Test
  public void parse_rejectsATruncatedPacket() {
    byte[] data = bytes(LIBRARY_RESPONSE);

    assertThrows(IllegalArgumentException.class, () -> MdnsMessage.parse(data, data.length - 3));
  }

  @Test
  public void parse_rejectsANameThatPointsAtItself() {
    byte[] data = bytes("000000000001000000000000" + "c00c" + "000c0001");

    assertThrows(IllegalArgumentException.class, () -> MdnsMessage.parse(data, data.length));
  }
}
